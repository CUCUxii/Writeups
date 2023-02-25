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
## Modelo OSI

Los pasos de una conexión están ordenados en el modelo OSI, y va por capas, como una cebolla.

El modelo OSI va por capas. Se encarga de comunicar dos ordenadores de manera organizada, cada capa se encarga de que se realize correctamente cada
parte de la conexión (ejemplo una de las Ips, otra de los protocolos...).

Digamos que 192.168.0.1 se quiere comunicar con  192.168.0.2

- 1. **Application** -> Se encarga de los protocolos. Es decir cada aplicacion utiliza su protocolo (Firefox.exe utiliza http y https)  
- 2. **Presentation/Translation** -> Se encarga del formato de archivo (ej PNG), su compresión y encriptacion (ej SSL)  
- 3. **Session** -> se encarga del trafico de red, controla el "dialogo" (cuando se establece o termina una conexion) Tambien de la autenticacion  
- 4. **Transport** -> ¿Como se mandan los paquetes? Pocos y ordenados (TCP) o muchos y rapido (UDP)  
- 5. **Network** -> manda (enruta) los paquetes a la IP destino, dichos paquetes estan fragmentados en trozos.   
- 6. **Ethernet** -> Aqui se manejan las direcciones MACS.   
- 7. **Physical** -> Manda los datos en bits por medios como conectores, cables... (controlando su voltajes, frecuencia...)  


![OSI](https://user-images.githubusercontent.com/96772264/221376050-d4cf83ff-56cb-4f8e-bac6-906a7643c1c2.png)
