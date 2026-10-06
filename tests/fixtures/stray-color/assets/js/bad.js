/* A negative fixture. Every line here is a way a script can introduce a colour
   the rule forbids outside tokens.css. tests/checks/css-colors.sh asserts that
   scanning this directory FAILS; if it ever passes, the scan has a hole.

   The third line is the one that matters most: the snippet this project's mark
   animation grew from built hsl() from a hardcoded hue at run time, and a scan
   that only looked for hex would have called it clean. */
var hex = "#ff0000";
var functional = "rgb(1, 2, 3)";
var assembled = "hsl(" + hue + " 65% 50%)";
var modern = "oklch(0.5 0.1 275)";
var named = "red";
