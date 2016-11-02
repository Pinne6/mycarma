<?php
$zip = new ZipArchive;
$res = $zip->open('/home/carma/dati/DATA.zip');
if ($res === TRUE) {
  $zip->extractTo('/home/carma/dati/intra/');
  $zip->close();
  echo 'woot!';
} else {
  echo 'doh!';
}
?>