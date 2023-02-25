Lo primero ¿Que es un protocolo? Un protocolo es un conjunto de normas que siguen dos programas para comunicarse. 
Esas normas se hacen para que no se pierdan datos o haya seguridad entre otras cosas.

En las conexiones entre sistemas, se utilizan puertos (para identificar que programa recibe que conexión) y direcciones 
IP (direccion del ordenador a donde mandar el mensaje). 
Todo esto se manda en "archivos socket" (En linux como ejemplo /dev/tcp/10.10.10.43/80) es decir el ordenador escribe
en ese archivo socket y el sistema operativo se encarga de mandarlo a la dirección indicada. 
Todo esto lo hacen los programas automaticamente.
```
PAQUETE TCP
  ORIGEN:10.10.10.10:5000    cadena "Hola Mundo"    DESTINO:10.10.20.20:5001
```
Los pasos de una conexión están ordenados en el modelo OSI, y va por capas, como una cebolla.
```
1. Application -> Comunicaciones entre aplicaciones que usan protocolos como HTTP o FTP y envian data legible  
2. Presentation/Translation -> Data comprimida o encriptada que se envia por la red  
3. Session -> se encarga del trafico de red, controla el "dialogo" (cuando se establece o termina una conexion)  
4. Transport -> Reenvia paquetes que no se sabe si han llegado bien garantizando esto ultimo. Protocolos TCP-UDP  
5. Network -> manda (enruta) los paquetes a la IP destino, dichos paquetes estan fragmentados en trozos.  
6. Data LINk -> transforma los paquetes a bits. Aqui se manejan las direcciones MACS.  
7. Fisica -> topologia de una red (medios como conectores, cables... y sus detalles como voltajes, frecuencia...)  
```
