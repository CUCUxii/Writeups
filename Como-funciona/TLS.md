# ¿Qué es?

El protocolo SSL-TLS se implementa para conexciones https. Se encarga de encriptar el mensaje para que un tercero no pueda entenderlo si lo
intercepta

# ¿ Como funciona ?

1. Cuando un cliente se conecta a un servidor, el servidor le manda un certificado TLS (con una llave publica)
2. Si el cliente confia, le manda una contraseña encriptada con la llave publica que el servidor desencriptara con la suya privada. (TLS Handshake)
3. Despues de eso ya se continua la conexión. Cada mensaje se encripta con la publica y se desencripta con la privada.

# Certificados: 

Android
1. Certificado system -> /system/etc/security/cacerts
2. Usuario -> /data/misc/user/0/cacerts-aded/ -> certificados manualmente instalados por el usaurio.
3. De la aplicacion -> /res/raw/certificate.der


