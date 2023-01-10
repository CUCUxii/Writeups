# Dont Over React
-----------------

Descargamos la apk -> app-release.apk

Para meterla en nuestro dispositivo Anbox ```adb install app-release.apk```
```console
└─$ adb install app-release.apk
Performing Streamed Install
Success
```
Al abrir la apk con el emulador solo nos encontramos el logo de "Hack the Box" y al desemsamblarla con jadx-gui
en /com/MainActivity tampoco había nada.
Solo queda grepear
```
└─$ apktool d app-release.apk
└─$ cd app-release.apk
└─$ grep -riE "hackthebox|dont over react"
assets/index.android.bundle:__d(function(g,r,i,a,m,e,d){Object.defineProperty(e,"__esModule",{value:!0}),e.myConfig=void 0;var t={importantData:"baNaNa".toLowerCase(),apiUrl:'https://www.hackthebox.eu/',debug:'SFRCezIzbTQxbl9jNDFtXzRuZF9kMG43XzB2MzIyMzRjN30='};e.myConfig=t},400,[]);
└─$ echo "SFRCezIzbTQxbl9jNDFtXzRuZF9kMG43XzB2MzIyMzRjN30=" | base64 -d
# La flag -> HTB{23m41n_c41m_4nd_d0n7_0v32234c7}
```

----------------------

# APK Crypt

Si instalamos la app en el emulador nos topamos con que nos piden una clave que no sabemos.

```java
public void onClick(View view) {
	if (MainActivity.md5(MainActivity.this.ed1.getText().toString()).equals("735c3628699822c4c1c09219f317a8e9")) {
       	Toast.makeText(MainActivity.this.getApplicationContext(), MainActivity.decrypt("k+RLD5J86JRYnluaZLF3Zs/yJrVdVfGo1CQy5k0+tCZDJZTozBWPn2lExQYDHH1l"), 1).show();
    } else {
        Toast.makeText(MainActivity.this.getApplicationContext(), "Wrong VIP code!", 0).show();
       
public static String encrypt(String str) throws Exception {
	Key generateKey = generateKey();
    Cipher cipher = Cipher.getInstance("AES");
    cipher.init(1, generateKey);
    return Base64.encodeToString(cipher.doFinal(str.getBytes("utf-8")), 0);}

public static String decrypt(String str) throws Exception {
    Key generateKey = generateKey();
    Cipher cipher = Cipher.getInstance("AES");
    cipher.init(2, generateKey);
    return new String(cipher.doFinal(Base64.decode(str, 0)), "utf-8");}

private static Key generateKey() throws Exception {
    return new SecretKeySpec("Dgu8Trf6Ge4Ki9Lb".getBytes(), "AES");}
```
El codigo VIP es un MD5 (735c3628699822c4c1c09219f317a8e9) que no podemos romper.

/snap/bin/anbox launch --package=org.anbox.appmgr --component=org.anbox.appmgr.AppViewActivity

```console
└─$ apktool d APKrypt.apk
└─$ cdAPKrypt/smali/ 
└─$ grep -rIE "735c3628699822c4c1c09219f317a8e9"    
APKrypt/smali/com/example/apkrypt/MainActivity$1.smali:    const-string v0, "735c3628699822c4c1c09219f317a8e9"

└─$ echo -n "cucuxii" | md5sum
1a5bf49db4c2f7f4cf8f1645e1fd3cc5
└─$ vim "APKrypt/smali/com/example/apkrypt/MainActivity\$1.smali"
```
```    
59     const-string v0, "1a5bf49db4c2f7f4cf8f1645e1fd3cc5"
65     if-nez p1, :cond_0
```
Ya una vez editado esto se tendría que compilar otra vez con esta [versión](https://bitbucket.org/iBotPeaches/apktool/downloads/)
Tambien hay que firmarlo para que te lo acepte.
```console
└─$ java -jar apktool.jar b APKrypt -o APKrypt.apk  
└─$ keytool -genkey -v -keystore key.keystore -alias APKrypt_apk -keyalg RSA -keysize 2048 -validity 10000;
└─$ jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore key.keystore APKrypt.apk APKrypt_apk;
└─$ adb install APKrypt.apk
```
Dandonos la key al poner "cucuxii"

-----------------------------
# Pinned

Esta app tiene guardados mis credenciales y me logueo automaticamente. Intente interceptar la peticion de login
y recuperar mi contraseña pero es una conexión segura. ¿Puedes ayudarme a bypasear la restricción de seguridad y
obtener la contraseña en texto plano?

Segun esto estamos tratando con un certificado TLS/SSL que encripta los datos para que nadie que no sea el cliente
o servidor los entienda (ya que no posee las llaves correspondientes)

Si abrimos la apk con jadx-gui (desensamblador) vemos en /com/example.pinned/MainActivity

```
	HttpsURLConnection httpsURLConnection2 = (HttpsURLConnection) new URL("https://pinned.com:443/pinned.php").openConnection();
    httpsURLConnection2.setRequestMethod("POST");
    httpsURLConnection2.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
    if (!mainActivity.s.getText().toString().equals("bnavarro") || !mainActivity.t.getText().toString().equals("1234567890987654")) {
        StringBuilder g2 = c.a.a.a.a.g("uname=bnavarro&pass=");
```
Con esta informacion probamos a hacer una peticion curl pero nada.
```console
└─$ curl -s -X POST "https://pinned.com:443/pinned.php" -d "uname=bnavarro&pass=1234567890987654"  
```
```console
└─$ /snap/bin/anbox launch --package=org.anbox.appmgr --component=org.anbox.appmgr.AppViewActivity
└─$ adb install pinned.apk
```
En Wireshark nos dice que la ip a la que va es la 3.64.163.50. Hay comunicaciones por TLS que nos dicen 
"Certificado desconocido" y se corta la conexión. 

La ip de nuestro movil emulado es 192.168.250.2
Con bupruiste nos descargamos su certificado en formato der (cert.crt)

sdcard/DOwnload

```console
└─$ adb shell settings put global http_proxy 192.168.250.1:6666

└─$ 7z x frida-server.xz;
└─$ adb push frida-server /data/local/tmp/
└─$ adb shell                                                  
x86_64:/ $ cd /data/local/tmp
x86_64:/data/local/tmp $ chmod 7555 frida-server
x86_64:/data/local/tmp $ ./frida-server  
```

Para instalar frida-tools como por pip o pip3 falla
Me descargue la [release](https://mirrors.aliyun.com/pypi/simple/frida-tools/)

```console
└─$ 7z x frida-tools-9.2.5.tar # cd luego a ello
└─$ ls # ->  frida_tools   frida_tools.egg-info   PKG-INFO   README.md   setup.cfg   setup.py
└─$ sudo python3 ./setup.py install

└─$ adb push cert.crt "/data/local/tmp/cert-der.crt"
└─$ frida -U \
  --codeshare "pcipolloni/universal-android-ssl-pinning-bypass-with-frida" \
  -f "com.example.pinned"
```


