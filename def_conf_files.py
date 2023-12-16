#------------------------------------------------------------------------------------------
# Autor: Alberto Valero Mlynaricova
# Fecha: 16/12/2023
#
# Descripción:  Este programa contiene las funciones relacionadas con los ficheros de configuración 
#               necesarios para hacer una conexión a un dominio usando samba
#------------------------------------------------------------------------------------------
import subprocess

def hosts_file(netbios, dominio, ip_host, destino):
    try:
        resultado_hostname = subprocess.run(["hostname"], capture_output=True, text=True)

        # Obteniendo el nombre de host actual desde la salida del comando (strip() elimina todos los espacios)
        hostname_old = resultado_hostname.stdout.strip()

        subprocess.run(["hostnamectl", "set-hostname", netbios])  # Cambia el hostname de la máquina

        with open(destino, 'r') as lee_hosts:
            lineas = lee_hosts.readlines()

        # Sustituye el nombre de host en cada línea
        lineas_modificadas = [linea.replace(hostname_old, netbios) for linea in lineas]

        with open(destino, "w") as escribe_hosts:
            for linea in lineas_modificadas:
                escribe_hosts.write(linea)  # Va sobreescribiendo el fichero con las líneas que tenía antes
                if "127.0.0.1" in linea:
                    escribe_hosts.write(f"{ip_host} {netbios}.{dominio} {netbios}\n")

    except Exception as e:
        print(f"Error en el paso de /etc/hosts: {e}")     
        
def resolv_file(dominio, destino):   
    try:
        with open(destino, "w") as escribe_resolv:
            escribe_resolv.write(f"domain {dominio}\nsearch {dominio}\nnameserver 192.168.100.3\n")
    except Exception as e:
        print(f"Error en el paso de /etc/resolv.conf: {e}")        

def samba_file(netbios, dominio, destino, default):
    try:
        # Leer el contenido del archivo
        with open(default, 'r') as lee_smbdefault:
            lineas = lee_smbdefault.read()

        # Realizar las sustituciones
        lineas_modificadas = (
            lineas
            .replace('nombrenetbios', netbios)
            .replace('COMPONENTE1', dominio.split('.')[0].upper())
            .replace('DOMINIO', dominio.upper())
        )

        # Escribir el contenido modificado de nuevo en el archivo
        with open(destino, 'w') as escribe_smb:
            escribe_smb.write(lineas_modificadas)
    except Exception as e:
        print(f"Error en el paso de /etc/samba/smb.conf: {e}")
            
def krb5_file(netbios, dominio, destino, default):
    dc = "serverad"

    try:
        # Leer el contenido del archivo
        with open(default, 'r') as lee_krb5default:
            lineas = lee_krb5default.read()

        # Realizar las sustituciones
        lineas_modificadas = (
            lineas
            .replace('DOMINIO', dominio.upper())        # Ejm: SUSPENSOS.COM
            .replace('dc.dominio', f'{dc}.{dominio}')   # Ejm: serverad.suspensos.com
            .replace('dominio', dominio)                # Ejm: suspensos.com
            .replace('.dominio', f'.{dominio}')          # Ejm: .suspensos.com
        )

        # Escribir el contenido modificado de nuevo en el archivo
        with open(destino, 'w') as escribe_krb5:
            escribe_krb5.write(lineas_modificadas)        
    except Exception as e:
        print(f"Error en el paso de /etc/krb5.conf: {e}")  