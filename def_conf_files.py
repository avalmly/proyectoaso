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
        encontrada_configuracion = False
        with open(destino, 'r') as file:
            lines = file.readlines()

        with open(destino, 'w') as file:
            for line in lines:
                # Elimina la línea que contiene "dhcp" específicamente para la interfaz especificada
                if "dhcp" in line.lower() and interfaz in line:
                    eliminado_dhcp = True
                    continue

                # Verifica si ya hay una configuración similar
                if interfaz in line and "inet static" in line:
                    encontrada_configuracion = True
                    break

                file.write(line)

            if not eliminado_dhcp and not encontrada_configuracion:
                # Si no se encontró y eliminó la configuración DHCP, y no se encontró una configuración similar, agrega la nueva configuración
                file.write(configuracion_nueva)
    except Exception as e:
        print(f"Error en el paso de /etc/network/interfaces: {e}")

# Llamada a la función
dominio = "prueba.com"
ruta_archivo = "/etc/network/interfaces"
interfaz = "enp0s3"
ip_host = "192.168.100.2"
static_ip(dominio, ruta_archivo, interfaz, ip_host)
