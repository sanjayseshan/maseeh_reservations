<html>
<head><title>Diagnostics</title></head>
<body>
<!--<h1>Browser Detection</h1>
<p>
<?php
 print 'You are using <b>' . $_SERVER['HTTP_USER_AGENT'] . '</b> from <b>'
     . $_SERVER['REMOTE_ADDR'] . '</b> (<b>'
     . gethostbyaddr($_SERVER['REMOTE_ADDR']) . '</b>).';
?>
</p>-->
<h1>Certificate Detection</h1>
<p>
<?php
 if (@$_SERVER['SSL_CLIENT_S_DN_CN']) {
  print 'Welcome, <b>' . $_SERVER['SSL_CLIENT_S_DN_CN'] . '</b>.<br>'
      . 'A certificate for <b>' . $_SERVER['SSL_CLIENT_S_DN_Email'] . '</b>'
      . ', issued by the <b>' . $_SERVER['SSL_CLIENT_I_DN_O']
      . '</b>, is correctly installed on your browser.<br>'
      . 'Your certificate will expire on ' . $_SERVER['SSL_CLIENT_V_END'] . '.';
 } else {
  ?>No certificate has been detected. Please ensure you are accessing
  <a href="https://geofft.scripts.mit.edu:444/detect.php">http<b>s</b>://geofft.scripts.mit.edu<b>:444</b>/detect.php</a>.<?php } ?>
</p>
<!--<h1>Server Detection</h1>
<p>
<?php
 exec('/sbin/ifconfig eth0', $ifconfig);
 $server_ip = preg_replace('/.*inet addr:([0-9\.]*).*/', '$1', $ifconfig[1]);
 print 'You are currently connected to <b>'
     . gethostbyaddr($server_ip) . '</b> (' . $server_ip
     . ').<br><pre>';
 system('/sbin/ifconfig eth0');
 print '</pre>';
?>-->
<?php 
echo $_SERVER['SSL_CLIENT_S_DN_Email']; echo ",";echo $_SERVER['SSL_CLIENT_S_DN_CN']; 

?>


<pre>

<?php
    # --- ENCRYPTION ---

    # the key should be random binary, use scrypt, bcrypt or PBKDF2 to
    # convert a string into a key
    # key is specified using hexadecimal
    
    $key = pack('H*', "PUT YOUR KEY HERE");
    # show key size use either 16, 24 or 32 byte keys for AES-128, 192
    # and 256 respectively
    $key_size =  strlen($key);
    echo "Key size: " . $key_size . "\n";
    
    $plaintext = "This string was AES-256 / CBC / ZeroBytePadding encryptedXXX.";
    $plaintext = $_SERVER['SSL_CLIENT_S_DN_Email'].",".$_SERVER['SSL_CLIENT_S_DN_CN'];

    # create a random IV to use with CBC encoding
    echo $plaintext."\n";
    $iv_size = mcrypt_get_iv_size(MCRYPT_RIJNDAEL_128, MCRYPT_MODE_CBC);
    $iv = mcrypt_create_iv($iv_size, MCRYPT_RAND);

  

    # creates a cipher text compatible with AES (Rijndael block size = 128)
    # to keep the text confidential 
    # only suitable for encoded input that never ends with value 00h
    # (because of default zero padding)
    $ciphertext = mcrypt_encrypt(MCRYPT_RIJNDAEL_128, $key,
                                 $plaintext, MCRYPT_MODE_CBC, $iv);

    # prepend the IV for it to be available for decryption
    $ciphertext = $iv . $ciphertext;
    
    # encode the resulting cipher text so it can be represented by a string
    $ciphertext_base64 = base64_encode($ciphertext);

    echo  urlencode($ciphertext_base64) . "\n";

    # === WARNING ===

    # Resulting cipher text has no integrity or authenticity added
    # and is not protected against padding oracle attacks.
    
    # --- DECRYPTION ---
#    $ciphertext_base64 = "e59AzieUrrhcu92kpGibrgfXvLxn8xDVviuhWZZp7pPjM3hrr4bkJJjUjsd9xqyLg5SQ7alylHYNLukWuWmx9biqw8Sq+BscEzYGGWTW5NA=";
    
    $ciphertext_dec = base64_decode($ciphertext_base64);
    
    # retrieves the IV, iv_size should be created using mcrypt_get_iv_size()
    $iv_dec = substr($ciphertext_dec, 0, $iv_size);
    
    # retrieves the cipher text (everything except the $iv_size in the front)
    $ciphertext_dec = substr($ciphertext_dec, $iv_size);

    # may remove 00h valued characters from end of plain text
    $plaintext_dec = mcrypt_decrypt(MCRYPT_RIJNDAEL_128, $key,
                                    $ciphertext_dec, MCRYPT_MODE_CBC, $iv_dec);
    
    echo  $plaintext_dec . "\n";
?>

</pre>
Verify at <a href="https://seshan.scripts.mit.edu/certdec.php?auth=<?php echo urlencode($ciphertext_base64); ?>">https://seshan.scripts.mit.edu/certdec.php?auth=<?php echo urlencode($ciphertext_base64); ?></a>
</body>
<script>
window.parent.postMessage("<?php echo urlencode($ciphertext_base64); ?>", "*");
</script>
</html>
