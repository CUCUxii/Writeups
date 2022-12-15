# Investigacion: Protocolos de internet

Lo primero ¿Que es un protocolo? 
Un protocolo es un conjunto de normas que siguen dos programas para comunicarse. Esas normas se hacen para que no se pierdan datos o haya seguridad entre otras cosas.

En las conexiones entre sistemas, se utilizan puertos (para identificar que programa recibe que conexión) y direcciones IP (direccion del ordenador a donde mandar
el mensaje). Todo esto se manda en "archivos socket" (En linux como ejemplo **/dev/tcp/10.10.10.43/80**) es decir el ordenador escribe en ese archivo socket y el
sistema operativo se encarga de mandarlo a la dirección indicada.

Los pasos de una conexión están ordenados en el modelo OSI, y va por capas, como una cebolla.

1. Application -> Comunicaciones entre aplicaciones que usan protocolos como HTTP o FTP y envian data legible  
2. Presentation/Translation -> Data comprimida o encriptada que se envia por la red  
3. Session -> se encarga del trafico de red, controla el "dialogo" (cuando se establece o termina una conexion)  
4. Transport -> Reenvia paquetes que no se sabe si han llegado bien garantizando esto ultimo. Protocolos TCP-UDP  
5. Network -> manda (enruta) los paquetes a la IP destino, dichos paquetes estan fragmentados en trozos.  
6. Data LINk -> transforma los paquetes a bits. Aqui se manejan las direcciones MACS.  
7. Fisica -> topologia de una red (medios como conectores, cables... y sus detalles como voltajes, frecuencia...)  


----------------------------------------
# Protocolo TCP
El protocolo TCP (Protocolo de Control de Transmision) se usa para mandar datos (paquetes) via web. 

1. Se encarga de comprobar que no se pierdan datos (paquetes) en el camino y valida siempre la conexión  
2. Numera los paquetes para que se reordenen.  
3. Tiene un checksum para comprobar que no se corrompan  
4. Comprueba que hay memoria suficiente para recibir todos los paqeutes  
5. Es algo mas lento que el UDP, asi que mejor para datos de texto.  

![tcp8](https://user-images.githubusercontent.com/96772264/207854226-3652f00a-9e79-4a14-805e-e00f170befa2.PNG)
*En esta imagen vemos todos los datos de una petición TCP, entre ellos numeros de secuencia para ordenar paquetes, puertos de entrada y salida y una función
checksum que opera con los bytes del mensaje para ver que no se han modificado los datos por el camino*

--------------------------------------------
## Anatomia de una conexion TCP
TCP antes de mandar los datos hace lo que se llama **handshake** o apreton de manos en tres pasos, para asegurarse de que se está manteniendo la conexión por ambas
partes (cliente y servidor)
**Reconocimiento:**  
1. Cliente    ------------------> SYN ------------------>  Servidor    (DATOS: MAC, tipo (Ipv4 o Ipv6), IPs y puertos (cliente, servidor), protocolo (6 es TCP))   
2. Cliente    <------------------ SYN,ACK <--------------  Servidor    (El servidor recibio la peticion)   
3. Cliente    ------------------> ACK ------------------>  Servidor    (El cliente recibio el paquete)  
**Datos**   
4. Cliente    <------------------ PSH,ACK <--------------  Servidor    (Los datos en si)  
5. Cliente    ------------------> ACK ------------------>  Servidor    (El cliente recibio los datos)  

![tcp5](https://user-images.githubusercontent.com/96772264/207855039-3337c2cd-2c3a-47a2-92c5-ea83510feac3.PNG)
*Ejemplo de captura con wireshark, se ve como hay primero el handshake y luego se mandan los datos*

El tamaño de cada paquete de datos (pareja de PSH,ACK y ACK) es limitado asi que si este es muy largo, se divide el mensaje en trozos y se manda esas partes.
Por ultimo tenemos el cierre de la conexión, es decir el handshake de despedida.
6. Cliente    ------------------> FIN,ACK -------------->  Servidor    (Cierro la conexion)
4. Cliente    <------------------ FIN,ACK <--------------  Servidor    (Cierro la conexion)
5. Cliente    ------------------> ACK ------------------>  Servidor    (Ok)

----------------------------------------
# Protocolo HTTP:

El protocolo HTTP va despúes del TCP, serían los datos en sí.
Cuando visitamos una web, le decimos a un ordenador (el servidor) que nos manden recursos. Esos recursos son código fuente de la web (o sea texto):  
![tcp2](https://user-images.githubusercontent.com/96772264/207856482-d3b8c438-b372-44aa-9721-2850f6d824b1.PNG)
*En este ejemoplo el codigo fuente de la web y un icono (el cuadradito de "remeber me")* 

![tcp10](https://user-images.githubusercontent.com/96772264/207855793-423c60d0-bbc9-4b6a-8180-348508ea8b2f.PNG)

Que nuestro navegador (firefox, opera, chrome...) se encarga de poner "bonito" para el ususario. Es decir, poniendo fotos, botones y esas cosas que dice el codigo
fuente donde hay que poner (en concreto suelen ser los archivos CSS)
![tcp6](https://user-images.githubusercontent.com/96772264/207855987-fefae2fd-5db6-4ae6-b58b-197c8d7c7e7c.PNG)

Pero el usaurio solo ve una reducida parte de lo que se envía, es decir, los datos "usaurio" y "contraseña". Si interceptamos una petición con programas como burpsuite
![tcp4](https://user-images.githubusercontent.com/96772264/207856139-d6475ce2-4c2b-4c87-924a-9bfce0e30a87.PNG)

Vemos que a parte de los datos, estamos mandando mas cosas como el tipo de petición (POST) el User Agent (programa para conectarnos), nuestra IP, el tamaño del
contenido... Digamos que todo está simplificado para que se mande automaticamente y no resulte tedioso para el usaurio comun.

![tcp7](https://user-images.githubusercontent.com/96772264/207856982-bf26c916-092f-4ec1-bf15-d66dafcbd2c5.PNG)
*Aqui se ve lo mismo con el programa de Wireshark, ademas abajo del todo está como literalmente manda el sistema esto, por bytes*

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




