
## Interfaces de red

La IP es un identificador de un equipo en una red, pero un ordenador puede estar conectado a redes diferentes, dichas conexiones son independientes, por lo que usan
interfaces distintas. Un ordenador puede estar conectado a la vez a una red local (LAN), a si mismo (localhost) y a una VPN por ejemplo. Si tiene una tarjeta de red
externa (la tipica Tp-link) es otra interfaz más

 - Red Local "LAN"
Esa red la constituyen todos los equipos conectados a un mismo punto de acceso (un router), suele empezar por "192.168.1"   
Cada dispotivo tiene una ip dentro de la LAN (IP privada) pero luego todos esos dispositivos salen a internet por el router con una misma IP pública. 
Todo esto lo hace el "NAT" (traductor de direcciones) del router

 - VPN 

#### VPN
Una VPN es una conexion a una LAN (red local) pero remota, es decir, te conectas no desde tu ubicacion sino desde la que esté esa LAN, como si cogieras un cable
gigantesco desde tu ordenador en Argentina y lo conectaras a un router en EE.UU, por tanto sales a internet desde allí (EE.UU), sirve por tanto para burlar
las restricciones locales, tambien ofrece mucha seguridad ya que una conexion por VPN siempre se cifra. Una VPN al ser como un router remoto, tambien te permite 
acceder a una LAN cerrada al exterior.

--------------------------------------------------------------------

## Direcciones IP

Una IP es un identificador de un equipo en una red.   
En **ipv4** Consta de 4 numeros (octetos) separados por "." del 0 al 255 (por tanto 1 byte cada uno = 8 bits) Cada ipv4 son 4 bytes 32 bits.

- **Publica** -> Como son limitadas se hacen a nivel de router (cada router posee una IP privada y todos los dispositivos conectados a el acceden por la misma)  
- **Privada** -> A nivel de LAN o red (dispositivos bajo un mismo router). El dispositivo con la ip privada "X.X.X.X" de una LAN es diferente al mismo de otra.  
El "NAT" se encarga de traducir direcciones ip privadas a publicas y vicebersa. La ip privada no tiene conectividad con internet asi que necesita que a la publica

Ej -> \[IP publica 142.150.0.0] ->  \[192.168.1.128 PC Antonio] - \[192.168.1.129 Movil Alba] - \[192.168.1.129 PC Berta]  
      \[IP publica 126.59.66.125] ->  \[192.168.1.128 PC Maite] - \[192.168.1.129 Movil Amador] - \[192.168.1.129 Movil Carlota]  

 - Direcciones IP "especiales" -> son direcciones tipicas que sirven para determinadas cosas  
    * 127.0.0.1 -> La loopback, una conexion que hace el sistema hacia si mismo (no accesible desde fuera) Usos: direcciones web en produccion.    

**IPV6** -> Ips mas largas (se crearon por si se acaban las otras). Utiliza numeros hexadcimales (0-F) Consta de 8 sets de 16 bits (128 bit/16bytes)  
8 grupos de 4bytes separados por ":"


#### Mascara de Subred 
Las IPs estan divididas en dos partes, la parte de la **red** y la del **host**. La "mascara de Subred" permite separar los octetos de la red de los del host.

1. 255.0.0.0 /8 → Clase A -> redes grandes, corporativas (muchos dispositivos) →  1 - 126 -> 10.0.0.0 - 10.255.255.255
2. 255.255.0.0 /16 → Clase B -> redes medianas (ejemplo universidades)  → 128 - 191  -> 172.16.0.0 - 172.31.255.255
3.	255.255.255.0 /24 → Clase C -> redes domesticas (pocos dispositivos)  → 192 - 223  -> 192.168.0.0 - 192.168.255.255

Las / son maneras abreviadas por tanto de indicar la mascara de subred, indican cuantos "1" tiene la IP (siempre de izquierda a derecha y nunca hay 0 antes que 1)   
Ej. 1 *En 255.0.0.0 son 8*
Ej. 2  *20.80.30.168/27  tiene la mascara 255.255.255.224 →  (11111111.11111111.11111111.11111110), = 27 “1”s Como tiene 3 “255” es de clase C*

#### Default Gateway
La pasarela es el sitio de donde saca tu sistema internet, o sea el router (indica su IP). Las IPs de los router suelen ser acabar en "192.168.0.1"
En una LAN dividida en dos (192.168.0.X y 192.168.1.X) hay dos pasarelas (192.168.0.1 y 192.168.1.1)

-----------------------------------------------------------------------

### Direccion MAC

Cada dispositivo que se puede conectar a internet debe tener un componente fisico (hardware) llamado "tarjeta de red", cada unz tiene un identificador, (la MAC)  
Cada MAC la componen 48 bits en numeros y letras (6 caracteres hexadecimales de 8 bits)  
Los tres primeros octetos son el OUI, identifican al fabricante de la tarjeta, los otros los asigna el fabricante para identificar la tarjeta.  
La dirección MAC es única e irrepetible.


### Segmento de red
Una red se suele dividir entre partes independientes para su menjor manejo. Cada parte es un segmento de red.
Esta division de una red en partes mas pequeñas se llama "Subneteo"

-----------------------------------------------------------------------

### DHCP

El DHCP es un servidor que asigna las IPS, mascaras, pasarleas y servidor DNS a los ordenadores. Dichas direcciones IPS están cedidas para que no se agoten 
(es decir se vuelven a repartir cada cierto tiempo), ya que si fueran fijas y se retira un ordenador de la red, se llevaria consigo la IP

### DNS

Dns o domain resolution service es un servidor intermediario (normalmente gestionado por nuestro provedor de internet) al que le hacemos peticiones mandandole strings
(direcciones web) y este nos contesta con la IP correspondiente, a la que se le hace la petición. Suele guardar en cache la traduccion para no saturarse de trabajo 
(tirando asi de memoria literalmente).

### ARP
ARP es *adress resolution protocol*, se encarga de traducir IPs a direcciones MAC (ya que son estas ultimas las que se encargan fisicamente de la conexión). Si la MAC
no esta todavia en la cache, el ordenador mandará una peitición preguntando a quien le corresponde que MAC en la LAN.

### WINS
Exlucivo de Windows. Relaciona IPs con nombres como "Ordenador Antonio"

### PAT
*"Port Adress Translation"*. Si todos los equipos de la LAN comparten origen (router) por el que pasan sus comunicaciones ¿Como sabe luego que conexion corresponde a 
que ordenador?  Gracias al PAT. La peiticon https de "PC Antonio" va por el puerto 4000, el de PC-Berta por el 4001... (PAT)   
```
\[IP publica 142.150.0.0]  
142.150.0.0:4001 ->  \[192.168.1.128 PC Antonio]   
142.150.0.0:4002 ->  \[192.168.1.129 Movil Alba]  
142.150.0.0:4002 ->  \[192.168.1.129 PC Berta]    
```

--------------------------------------------------------------------

## Puertos y servicios mas comunes 

Un puerto no es mas que el identificador de una conexión. Un ordenador puede tener 65535 (2^16) conexiones diferentes. Cualquier servicio en linea se peude asignar a 
cualquier puerto, pero hay convenciones, es decir, puertos que se suelen poner por defecto.

 - Protocolo HTTP/HTTPS (web) -> 80, 443, 8080   
 - Protocolo SSH (control remoto) -> 22  
 - DNS (servidor de resolucion de dominios) -> 53  
 - Kerberos (Directorio activo) -> 88  
 - POP mail (recibir) -> 110  
 - SMTP mail (enviar) -> 25  
 - Base de datos SQL -> 3306  
 - Minecraft -> 25565  
 - FTP (compartir archivos) -> 21  
 - DHCP (gestion de IPs privadas en una LAN) -> 67, 68   
 - SNMP (gestion de redes) -> 161   
 - SMB (compartir archivos) ->  137  
 - NFS (compartir archivos) -> 2049   
  
--------------------------------------------------------------------

## Modelo OSI

Separa la comunicacion entre ordenadores entre diferentes capas. Cuando dos computadoras se quieren comunicar tienen que pasar por todas estas capas en orden.

7. Application -> Comunicaciones entre aplicaciones que usan protocolos como HTTP o FTP y envian data legible
6. Presentation/Translation -> Data comprimida o encriptada que se envia por la red 
5. Session -> se encarga del trafico de red, controla el "dialogo" (cuando se establece o termina una conexion)
4. Transport -> Reenvia paquetes que no se sabe si han llegado bien garantizando esto ultimo. Protocolos TCP-UDP
3. Network -> manda (enruta) los paquetes a la IP destino, dichos paquetes estan fragmentados en trozos.
2. Data LINk -> transforma los paquetes a bits. Aqui se manejan las direcciones MACS.
1. Fisica -> topologia de una red (medios como conectores, cables... y sus detalles como voltajes, frecuencia...)


--------------------------------------------------------------------

## SOCKETS

Los sockets son archivos en los que se escribe la data que se quiere enviar. Estos sockets (ejemplo con tcp) se encargan de enviar los bytes a la otra maquina
sin que el programador de turno tenga preocuparse por cuestiones mas complejos de la conexion como saltos y esas cosas. Todo eso lo hace el sistema operativo.
```
PAQUETE TCP
  ORIGEN:10.10.10.10:5000    cadena "Hola Mundo"    DESTINO:10.10.20.20:5001
```
Por ejemplo en Linux 


















