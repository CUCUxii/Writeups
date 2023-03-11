Lo primero ¿Que es un protocolo? Un protocolo es un conjunto de normas que siguen dos programas para comunicarse. 
Esas normas se hacen para que no se pierdan datos o haya seguridad entre otras cosas.

En las conexiones entre sistemas, se utilizan puertos (para identificar que programa recibe que conexión) y direcciones IP (direccion del
ordenador a donde mandar el mensaje). 
Todo esto se manda en "archivos socket" (En linux como ejemplo /dev/tcp/10.10.10.43/80) es decir el ordenador escribe en ese archivo socket y
el sistema operativo se encarga de mandarlo a la dirección indicada. Todo esto lo hacen los programas automaticamente.
```
PAQUETE TCP
  ORIGEN:10.10.10.10:5000    cadena "Hola Mundo"    DESTINO:10.10.20.20:5001
```
------------------------------------------
## Modelo OSI

Los pasos de una conexión están ordenados en el modelo OSI, y va por capas, como una cebolla.

El modelo OSI va por capas. Se encarga de comunicar dos ordenadores de manera organizada, cada capa se encarga de que se realize correctamente cada
parte de la conexión (ejemplo una de las Ips, otra de los protocolos...).

Digamos que 192.168.0.1 se quiere comunicar con  192.168.0.2

- 1. **Application** -> Es con la que inberactua el usaurio, define los protocolos que usan las aplicaciones (Firefox.exe -> http y https) 
- 2. **Presentation/Translation** -> Se encarga del formato de archivo (ej PNG), su compresión y encriptacion (ej SSL) traduce entre computadoras.
- 3. **Session** ->  se encarga del trafico de red, controla el "dialogo" (cuando se establece o termina una conexion) Tambien de la autenticacion  
- 4. **Transport** -> Controla el flujo de datos. Les pone una cabecera y los segmenta -> segmentos. Protocolos: TCP y UDP, Define los puertos logicos.
- 5. **Network** -> (enruta) los paquetes a la IP destino, de la manera mas optima, y les pone mas cabeceras entre ellas las IPs -> paquetes.  
- 6. **Ethernet** -> Encapsula los paquetes con un principio y un fin convirtiendolos en tramas. Aqui se manejan las direcciones MAC.   
- 7. **Physical** -> Manda los datos en bits por medios fisicos como cables... (controlando su voltajes, frecuencia...)  

![OSI](https://user-images.githubusercontent.com/96772264/224501387-83dcd02d-4899-4fe5-8588-ac0f9318facc.png)

------------------------------------------
## Modelo TCP/ip

Mientras que el OSI es un modelo de referencia, el TCP es el que se usa, mas que algo distinto es algo equivalente.
1. Capa de aplicacion (equivale a aplicacion, trasnporte y sesion) -> Aplicaciones de red como SMTP, HTTP, SMB...
2. Transporte (equivale a la de trasnporte) -> datos de enrutamiento (IP) y estado de la trasnmision (TCP, UDP)
3. Internet (Network) -> proporciona el paquete de datos o datagrama. Maneja direcciones IP.
4. Acceso (Ehternet y Fisica) -> se encarga de los medios fisicos y direcciones MAC, como se deben mandar segun el tipo de red.





