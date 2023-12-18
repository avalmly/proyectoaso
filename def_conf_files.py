#------------------------------------------------------------------------------------------
# Autor: Alberto Valero Mlynaricova
# Fecha: 18/12/2023
#
# Descripción:  Este programa contiene las funciones relacionadas con los ficheros de configuración 
#               necesarios para hacer una conexión a un dominio usando samba
#------------------------------------------------------------------------------------------
import subprocess
import re

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
                if not "127.0.1.1" in linea:
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

def static_ip(dominio, destino, interfaz, ip_host):
    try:
        configuracion_nueva = f"""
auto {interfaz}
iface {interfaz} inet static
    address {ip_host}
    netmask 255.255.255.0
    gateway 192.168.100.1
    dns-nameservers 192.168.100.3
    dns-search {dominio}
"""

        eliminado_dhcp = False
        with open(destino, 'r') as file:
            lines = file.readlines()

        with open(destino, 'w') as file:
            for line in lines:
                # Elimina la línea que contiene "dhcp" específicamente para la interfaz especificada
                if "dhcp" in line.lower() and interfaz in line:
                    eliminado_dhcp = True
                    continue
                file.write(line)

            if not eliminado_dhcp:
                # Si no se encontró y eliminó la configuración DHCP, agrega la nueva configuración
                file.write(configuracion_nueva)
    except Exception as e:
        print(f"Error en el paso de /etc/network/interfaces: {e}")

# Llamada a la función
dominio = "prueba.com"
ruta_archivo = "/etc/network/interfaces"
interfaz = "enp0s3"
ip_host = "192.168.100.2"
static_ip(dominio, ruta_archivo, interfaz, ip_host)


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
