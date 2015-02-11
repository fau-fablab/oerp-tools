<!DOCTYPE html>

<?php
	$githuburl = "https://github.com/fau-fablab/oerp-tools";
	$title = "OERP Tools";
	$script_folder = "../";
?>

<html>
    <head>
	    <meta charset="utf-8">

        <title>FAU FabLab - <?= $title ?></title>
	    <link rel="shortcut icon" href="https://fablab.fau.de/sites/fablab.fau.de/files/fablab_favicon.ico" type="image/x-icon">
        <link type="text/css" rel="stylesheet" media="all" href="https://user.fablab.fau.de/~ev80uhys/web/faufablab-light.css">	
    </head>
    <body>
         <div id="header" class="header">
             <div id="logo" class="logo">
                 <a href="https://fablab.fau.de">
                     <img src="https://fablab.fau.de/sites/fablab.fau.de/files/fablab_logo.png" alt="Startseite">
                 </a>
             </div>

             <div id="fork-on-github" style="position: fixed; top: 0; right: 0; border: 0;">
                 <a href="<?= $githuburl ?>">
                     <img src="https://camo.githubusercontent.com/52760788cde945287fbb584134c4cbc2bc36f904/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f77686974655f6666666666662e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_white_ffffff.png">
                 </a>
             </div>
         </div>

        <div id="top" class="top">
        </div>

        <div id="content" class="content">
            <h1>Webinterface for OERP-Tools</h1>
            <h2>Next available Product IDs:</h2>
            <pre style="text-size:150%">
<?php
    $ids = explode( PHP_EOL, trim( run_system_command( '/usr/bin/env python ' . $script_folder . 'nextprodid.py' ) ) );
    foreach ( $ids as $extr ) {
        print ' - ' . $extr . PHP_EOL;
    }
?>
            </pre>

	    <p>Choose one of these IDs and place it in the <code>internal reference</code> Field. You can find more infos <a target=”_blank” href="http://user.fablab.fau.de/~ak22emur/pdf-buildserver/public/output/Produkt_anlegen.pdf">here</a>.</p>
        </div>

<?php
    function run_system_command( $cmd ) {
        ob_start();
        passthru( escapeshellcmd( $cmd ) );
        return ob_get_clean();
    }
?>

        <div id="bottom" class="bottom">
            <h3>If you want to contribute, you can make a pull request on <a href="<?= $githuburl ?>">github</a>.</h3>
            <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" property="dct:title"><a href="<?= $githuburl ?>"><?= $title ?></a></span> by <a xmlns:cc="http://creativecommons.org/ns#" href="https://github.com/fau-fablab" property="cc:attributionName" rel="cc:attributionURL">FAU FabLab</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
        </div>
    </body>
</html>
