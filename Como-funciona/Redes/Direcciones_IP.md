# Direcciones IP

Una direccion IP identifica a un equipo en una red, existen dos tipos:
- Publica: todos los equipos bajo un mismo router acceden a esta bajo la misma IP. Es unica.
- Privada: Es la que tiene un dispositivo en una LAN, puede ser igual al de otro en otra LAN pero no tiene nada que ver.

A nivel de IP operan ciertos protocolos o mecanismos:
- El protocolo NAT: del router se encarga de la traduccion entre Privada y Publica.
- El protocolo DHCP: asigna automativcamente IPs en una LAN, estas son cedidas temporalmente y suelen varair. 
- El protocolo DNS: traduce IPs a nombres de dominio que se puedan recordar facilmente.

--------------------------------------
## Tamaño de redes:

La mascara de red permite saber el tamaño de una red:
- 255.255.255.00  /24 -> Se pueden conectar 256 dispositivos. Ej 192.168.0.136/24 -> direccion de red 192.168.0.00
- 255.255.00.00   /16 -> Se pueden conectar 2^16 dispositivos (65535) Ej 10.0.24.136/16 -> direccion de red 10.0.00.00
- 255.00.00.00    /8  -> Se pueden conectar 2^24 dispositivos (16 millones) 
Siempre hay tres direcciones reservadas especiales: la primera para la red, la segunda para el router o gatewat y la ultima para broadcast (a todos)

1. Si el numero en vez de ser "entero" (/24 /16 o /8) es otro, por ejemplo /19 se ve cuanto hay de diferencia (en este caso 3  16 + 3 = 19)
2. Esa diferencia si es 1 las IP van de 128 en 128, si es 2 de 64 en 64, si es 3 de 32 en 32...  128 > 64 > 32 > 16 > 8 > 4 > 2 > 1
3. Una vez veas los tramos, ej de 32 en 32, hay que ver a que tramo pertenece.
  * Por ejemplo 10.0.85.136/18 -> es de 64 en 64 -> 0  > 64 (85) < 128 -> red 10.0.64.00 - broadcast -> 10.0.127.255

--------------------------------------
## Ejemplo de Red LAN:

![red1](https://user-images.githubusercontent.com/96772264/226171431-80f87a21-2409-4cde-99f2-b2deaa8a21cc.png)

- Todos los dispositivos van a salir por una unica IP publica
- Si PC1 se quiere comunicar con PC2 lo hara por su red, mediante el switch
- Si PC1 se quiere comunicar con PC5 lo hara por el router ya que son redes diferentes pero se comunican por la gateway.
- En redes al siwitch y hub se les llama dominios del difusion mientras que los dispositivos finales (PCs) son los de colision.

## Protocolo ARP
Un equipo tiene dos direcciones, la IP(varaible) y la fisica o MAC(fija) que esta asociada a su tarjeta de red. Para realizar
una conexion se necesitan ambas. Ahi entra en juego el protocolo ARP, que permite traducir entre direcciones IP y MAC dentro de una LAN.

Cuando quiere saber la MAC de un dispositivo (ej PC 3 192.168.1.30) manda dicha IP a todos los dispositivos por la broadcast (192.168.1.255)
y el que tenga esa IP le contesta con su MAC (es decir PC 3) Las respuestas se guardan en la tabla ARP para proximas veces.

-----------------------------------
## Enrutamiento

Cuando un dispositivo de una LAN sale a internet, tiene que saber como llegar a la direccion destino. Para ello cuenta con su **tabla de rutas**
que le indica el camino. 
Si no lo sabe, le manda una peticion a la default gateway (o sea el router) que si que sabra como llegar. Eso se ve en la tabla de rutas como "0.0.0.0"

La tabla de rutas no solo dice como llegar sino por que interfaz salir, cual es el camino mas rapido (metrica, siendo la mas baja mas rapida) y 
cual es el siguiente salto.
> camino mas rapido: redes mas pequeñas, añadidas manualmente (estaticas) y el protocolo de enrutamiento dinamico con la metrica mas baja.

Un router solo conoce como llegar los routers mas proximos porque sus rutas se han configurado manualmente, pero tiene que conocer muchas mas rutas
si quiere mandar el paquete con exito al destino. Para ello actualiza su tabla de rutas por medio de:
 - Rutas estaticas: el administrador de redes las ha añadido manualmente, no varian y son mas seguras. No se anuncian ni propagan y consumen menos ancho de banda (recursos de red) por lo que son secretas para redes privadas. Aun asi son propensas a errores y mas dificiles de mantener.
 - Rutas dinamicas: los routers que conocen rutas, se las mandan a otros routers constantemente, eso hace que se puedan actualizar rapidamente a cambios. Todo esto se realiza con los protocolos de routing dinamico (ripv2, ospf, bgpv, eigrp...)










