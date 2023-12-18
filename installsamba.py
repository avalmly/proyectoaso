#------------------------------------------------------------------------------------------
# Autor: Alberto Valero Mlynaricova
# Fecha: 16/12/2023
#
# Descripción:  script con el siguiente formato:
#                   $ sudo installSamba host5 prueba.com administrator Departamento1!
#
#               Cambiará el nombre de la máquina a host5, instalará todo lo necesario para   
#               disponer de samba, kerberos. Modificará el fichero smb.conf, krb5.conf, 
#               nsswitch. Después unirá la máquina al dominio indicado (prueba.com) con las 
#               credenciales indicadas.
#------------------------------------------------------------------------------------------

import os
import sys
import subprocess
import re                 # Para usar expresiones regulares
from def_conf_files import hosts_file, resolv_file, krb5_file, samba_file


def pkg_ready(paquetes):
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'    #Hace que el trabaje en modo no interactivo, es decir, que no pedirá confirmaciones
    for paquete in paquetes:
        # Verificar si el paquete está instalado
        resultado = subprocess.run(f"dpkg -l | grep {paquete}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Si no se encuentra ninguna coincidencia, instalar el paquete
        if not resultado.stdout.strip():
            print(f"Instalando {paquete}...")
            subprocess.run(f"apt install -y {paquete}", shell=True) # La opción -qq a parte de forzar el sí hace que sea más silencioso con el output

        else:
            print(f"{paquete} ya está instalado.")

def obtener_ip(interfaz):
    try:
        resultado = subprocess.run(['ip', 'a', 'show', interfaz], capture_output=True, text=True)
        
        for linea in resultado.stdout.split('\n'):
            if 'inet' in linea:
                # Obtener la dirección IP de la línea
                ip = linea.split()[1].split('/')[0]
                return ip
            
    except (KeyError, IndexError) as e:
        print(f"No se pudo obtener la IP de la interfaz {interfaz}. Error: {e}")
        return None

paquetes = ["samba", "smbclient", "winbind", "krb5-kdc", "krb5-user", "krb5-config", "realmd", "libpam-winbind", "libnss-winbind"]
pkg_ready(paquetes)

netbios = sys.argv[1]
dominio = sys.argv[2]
usuario = sys.argv[3]
password = sys.argv[4]

rutas_conf = ["/etc/hosts", "/etc/resolv.conf", "/etc/samba/smb.conf", "/sbin/sambazings/smb-default.conf", "/etc/krb5.conf", "/sbin/sambazings/krb5-default.conf", "/etc/nsswitch.conf"]
ip_host = obtener_ip("enp0s3")

# Configuración de ficheros
hosts_file(netbios, dominio, ip_host, rutas_conf[0])
resolv_file(dominio, rutas_conf[1])
samba_file(netbios, dominio, rutas_conf[2], rutas_conf[3])
krb5_file(netbios, dominio, rutas_conf[4], rutas_conf[5])

os.system("systemctl restart smbd nmbd networking")
os.system(f"net ads join -U {usuario}%{password}")
os.system("systemctl restart winbind")
