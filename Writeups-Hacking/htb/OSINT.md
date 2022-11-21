Hack the box OSINT
------------------

El OSINT es la investigación de fuentes abiertas, es decir conseguir toda la información sobre alguien mediante 
internet (de manera legal como en busquedas de google dorks y redes sociales)

---------------------

# Reto 1: Easy Phish

"Los clientes de "secure-startup.com" han recibido emails de phising muy convincentes. ¿Podrias decir porque?"   
Es un .com así que no es nada de la red interna de Hack the Box. Si pongo esta url nos sale una página de GoDaddy
diciendo que está libre (o sea que no existe)

```console
└─$ dig secure-startup.com
secure-startup.com.	423	IN	A	34.102.136.180
└─$ whois 34.102.136.180
# Nos dice que es una plataforma de Google Cloud
```
Como tiene que ver con spoofing de correos, se puede tirar de **dmarc**
> **dmarc** -> protocolo que se encarga proteger contra el phising, desechando los correos que no cumplen las
> normas de verificación (posibles atacantes). Tambien guarda un registro TXT.

Con este comando dig nos puede enseñar los registros TXT de dmarc  
```console
└─$ dig TXT secure-startup.com _dmarc.secure-startup.com +short
"v=spf1 a mx ?all - HTB{RIP_SPF_Always_2nd"
"v=DMARC1;p=none;_F1ddl3_2_DMARC}"
```
Flag > "HTB{RIP_SPF_Always_2nd_F1ddl3_2_DMARC}"

-------------------------

# Reto 2: Infiltration

"Puedes encontrar alguna información que permita entrar en 'Evil Corp LLC' Tira sobre todo de redes sociales"

Si ponemos en google ```evil corp llc site:instagram.com```  
Acabamos en el perfil de esta señora:  
![osint1](https://user-images.githubusercontent.com/96772264/203130962-1852220a-50c2-4982-8ad8-545757936bd5.PNG)

En la 6ª foto (la del portatil) encontramos en pequeñito la FLAG
![osint2](https://user-images.githubusercontent.com/96772264/203130983-a5e72c65-a6e2-4d1f-aa9d-674bf8d9ebbe.PNG)







