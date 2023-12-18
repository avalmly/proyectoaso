#------------------------------------------------------------------------------------------
# Autor: Alberto Valero Mlynaricova
# Fecha: 16/12/2023
#
# Descripción:  Creará el recurso recurso1 solo permitirá conectarse a los usuarios del grupo   
#               alumnos que están disponible en directorio activo, en el caso de no existir el 
#               grupo será necesario crearlo usando powershell remoto al servidor de dominio
#------------------------------------------------------------------------------------------

import os
import sys
import subprocess    

def crear_grupo_ad(host, usuario, contrasena, grupo):
    try:
        # Rutas de las claves SSH
        private_key_path = os.path.expanduser("~/.ssh/id_rsa")

        # Verificar si la clave privada ya existe
        if not os.path.exists(private_key_path):
            # Generar clave privada y pública si no existen
            os.system(f"ssh-keygen -t rsa -f {private_key_path} -N ''")
            print("Claves generadas con éxito.")

        # Comando para copiar la clave pública al servidor
        copy_key_cmd = f"sshpass -p '{contrasena}' ssh-copy-id -i {private_key_path}.pub {usuario}@{host}"

        # Verificar si la clave pública ya está en el servidor
        result = os.system(copy_key_cmd)

        if result == 0:
            print("Clave pública copiada con éxito al servidor.")
        else:
            raise Exception("Error al copiar la clave pública al servidor.")

        # Comando de ejecución de PowerShell
        cmd_ssh = f'sshpass -p "{contrasena}" ssh {usuario}@{host} "powershell -NoProfile -NonInteractive -Command "New-ADGroup -Name {grupo} -GroupScope Global""'        
        
        # Ejecutar el comando
        subprocess.run(cmd_ssh, shell=True)
        print(f"Grupo '{grupo}' creado con éxito en Active Directory.")
    except Exception as e:
        print(f"Error al crear el grupo: {e}")


def check_grupo(host, usuario, contrasena, grupo):
    try:
        lista_grupos = subprocess.run(['getent', 'group'], capture_output=True, text=True)
        if grupo not in lista_grupos.stdout:
            print("El grupo especificado no existe. Creando grupo...")
            crear_grupo_ad(host, usuario, contrasena, grupo)
            os.system(f"systemctl restart winbind") # Para que aparezcan los nuevos grupos al hacer un getent
        else:
            print("El grupo ya existe")
    except subprocess.CalledProcessError:
        print("Error al obtener la lista de grupos")

def crea_recurso(recurso, ruta, grupo):
    try:
        with open("/sbin/plantilla_recurso", 'r') as plantilla_recurso:
            lineas = plantilla_recurso.read()

        # Realizar las sustituciones
        lineas_modificadas = (
            lineas
            .replace('recurso', recurso)
            .replace('ruta', ruta)
            .replace('grupo', grupo)
        )

        smb_conf_path = "/etc/samba/smb.conf"

        # Verificar si el recurso ya existe en smb.conf
        with open(smb_conf_path, 'r') as smb_conf:
            if f"[{recurso}]" not in smb_conf.read():
                # Añadir las líneas modificadas al archivo smb.conf
                with open(smb_conf_path, "a") as samba_file:
                    samba_file.write(f'\n{lineas_modificadas}\n')
                    
                # Verificar si el directorio ya existe antes de intentar crearlo
                if not os.path.exists(f"/recursos/{recurso}"):
                    # Crear el directorio del recurso
                    os.makedirs(f"/recursos/{recurso}")

                    # Configurar permisos del directorio
                    os.chmod(f"/recursos/{recurso}", 0o770)
                    os.system(f"chown :{grupo} /recursos/{recurso}")

                    print(f"Recurso '{recurso}' y directorio creado con éxito.")
                else:
                    print(f"El directorio '/recursos/{recurso}' ya existe.")
            else:
                print(f"El recurso '{recurso}' ya existe en smb.conf.")

    except FileNotFoundError:
        print("Error: No se encontró el archivo de plantilla 'plantilla_recurso'.")
    except Exception as e:
        print(f"Error durante la creación del recurso: {e}")


recurso = sys.argv[1]
grupo = sys.argv[2]
ruta = f"/recursos/{recurso}"
host = "serverad"
usuario = "administrador"
password = "Departamento1!"

check_grupo(host, usuario, password, grupo)
crea_recurso(recurso, ruta, grupo)
