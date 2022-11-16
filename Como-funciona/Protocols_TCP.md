# Investigacion: el protocolo TCP

El protocolo TCP (Protocolo de Control de Transmision) se usa para mandar datos (paquetes). 

1. Se encarga de comprobar que no se pierdan datos (paquetes) en el camino y valida siempre la conexión
2. Numera los paquetes para que se reordenen.
3. Tiene un checksum para comprobar que no se corrompan
4. Comprueba que hay memoria suficiente para recibir todos los paqeutes
5. Es algo mas lento que el UDP, asi que mejor para datos de texto.


## Anatomia de una conexion TCP

Reconocimiento
1. Cliente    ------------------> SYN ------------------>  Servidor    (MAC, tipo (Ipv4 o Ipv6), IPs y puertos (cliente, servidor), protocolo (6 es TCP))
2. Cliente    <------------------ SYN,ACK <--------------  Servidor    (El servidor recibio la peticion)
3. Cliente    ------------------> ACK ------------------>  Servidor    (El cliente recibio el paquete)
Datos
4. Cliente    <------------------ PSH,ACK <--------------  Servidor    (Los datos en si)
5. Cliente    ------------------> ACK ------------------>  Servidor    (El cliente recibio los datos)

El tamaño de cada paquete de datos (pareja de PSH,ACK y ACK) es limitado asi que se parte el mensaje en trozos y se manda otro paquete mas

6. Cliente    ------------------> FIN,ACK -------------->  Servidor    (Cierro la conexion)
4. Cliente    <------------------ FIN,ACK <--------------  Servidor    (Cierro la conexion)
5. Cliente    ------------------> ACK ------------------>  Servidor    (Ok)

------------------------------------------------------------

## FTP - 21
File Transfer Protocol, un protocolo para descarga de archivos como su nombre dice. Se usa mas en Linux porque Windows tiene el SMB para ello (445) 
El FTP puede ser un servidor especializado o un servicio corriendo en tu propio ordenador

------------------------------------------------------------

## SSH - 22 
El servicio ssh te permite conectarte y manejar un ordenador remotamente bajo un usaurio. La conexion, a diferencia del Telnet esta encriptada.
Con ssh se crea en el usuario actual una carpeta oculta llamda ".ssh" donde estan las llaves necesarias para conectarte. Si no quieres usar llaves te puedes 
conectar por contraseña.

- La llave privada *id_rsa*, si la otra persona tiene una copia de esa llave se puede conectar a tu ordenador bajo tu usaurio.
- La llave publica, que es la que tienes que meter tu en el archivo de *known_host* del ordenador al que te quieres conectar.
- El archivo "known_hosts".

## Telnet 23
Como el SSH pero mucho menos seguro y antiguo, ya esta en desuso

------------------------------------------------------------

## SMTP
Servicio para mensajeria. SMTP solo envia mensajes (no recibe). Los servicios como *Gmail* o *Outlook* son clientes smtp. Siempre garantiza que la direccion
a la que se mandan los paquetes exista.

------------------------------------------------------------

## DNS - 53
Se encarga de relacionar un nombre de dominio ej *google.com* con su IP para no tneer que aprenderse las IPs de memorieta y conectarse mas facilmente. 
En Linux, dicha correlacion se escribe a mano en el archivo */etc/hosts* para ciertas paginas que no sean tan publicas como *google.com*

------------------------------------------------------------

## Protocolo HTTP - 80
Suele correr en el puerto 80 por defecto.
El servicio "Apache" se suele encargar de gestionar un servidor que implemente http.
[Mas informacion de este protocolo](https://github.com/CUCUxii/Informatica/blob/main/Web/Protocolo_http.md)

------------------------------------------------------------

## Kerberos - 88
El puerto Kerberos se encarga de la seguridad en un dominio empresarial encriptando conexiones con llaves y capas de proteccion.

------------------------------------------------------------

## SMB/Samba - 445 
El SMB es un servicio de trasnferencia de archivos de Windows sobre una LAN, o sea un servicio para bajarte archivos o depositarlos en otro ordenador
Cuando un ordenador se autentica al puerto Samba manda un HASH identificativo llamado *NTLM* (la contraseña encriptada), es crucial que las conexiones se validen
para que nadie que no sea el ordenador legitimo reciba ese HASH.

------------------------------------------------------------

## SQL - 3306
El puerto que hostea bases de datos SQL

------------------------------------------------------------

## WINRM - 5986
El servicio WINRM es un aervicio de los sistemas Windows para conectarte remotamente a ellos (algo asi como el ssh).
Si el ordenador (ej de una empresa) tiene el WinRM abierto, los empleados se pueden conectar a él de manera remota proporcionando su nombre de usario,
IP y contraseña.

No todos los usaurios de una red pueden conectarse a este equipo sino solo los que esten el en grupo especial "Remote Management Users"

------------------------------------------------------------

## HTTPS - 8080
Version segura del HTTP, los datos estan encriptados por el certificado SSL. Pero hay sistemas que el SSL lo tienen autofirmado asi que es dudosamente seguro en esos
casos.

------------------------------------------------------------




