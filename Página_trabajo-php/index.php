<?php // index.php — Aromaris con Bootstrap 5 ?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Aromaris — Jabones Artesanales</title>

  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet"/>
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Jost:wght@200;300;400&display=swap" rel="stylesheet"/>

  <style>
    :root {
      --cream:    #f7f2eb;
      --sand:     #e8ddd0;
      --terra:    #c8735a;
      --terra-dk: #b56249;
      --dark:     #2e2a26;
      --muted:    #6a6460;
    }
    body { background:#faf8f4; color:var(--dark); font-family:'Jost',sans-serif; font-weight:300; }

    /* Tipografía */
    .font-display { font-family:'Cormorant Garamond',serif; }
    .section-tag  { font-size:.7rem; letter-spacing:.25em; text-transform:uppercase; color:var(--terra); }

    /* Colores Bootstrap override */
    .bg-cream  { background-color:var(--cream)  !important; }
    .bg-dark-c { background-color:var(--dark)   !important; }
    .text-terra{ color:var(--terra) !important; }

    /* Navbar */
    .navbar {
      background:rgba(250,248,244,.9) !important;
      backdrop-filter:blur(10px);
      border-bottom:1px solid rgba(200,180,160,.2);
    }
    .navbar-brand {
      font-family:'Cormorant Garamond',serif;
      font-size:1.75rem; font-weight:300; letter-spacing:.1em;
      color:var(--dark) !important;
    }
    .nav-link {
      font-size:.74rem; letter-spacing:.18em; text-transform:uppercase;
      color:var(--dark) !important; opacity:.65; transition:opacity .2s;
    }
    .nav-link:hover { opacity:1; }

    /* Botones */
    .btn-terra {
      background:var(--terra); color:#fff; border:none; border-radius:0;
      font-size:.74rem; letter-spacing:.18em; text-transform:uppercase;
      padding:.7rem 1.8rem; transition:background .25s, transform .2s;
    }
    .btn-terra:hover { background:var(--terra-dk); color:#fff; transform:translateY(-2px); }
    .btn-outline-c {
      border:1.5px solid var(--dark); background:transparent; border-radius:0;
      color:var(--dark); font-size:.74rem; letter-spacing:.18em; text-transform:uppercase;
      padding:.7rem 1.8rem; transition:background .25s, color .25s;
    }
    .btn-outline-c:hover { background:var(--dark); color:#fff; }

    /* Hero */
    .hero-section { min-height:100vh; padding-top:76px; }
    .hero-img-col { position:relative; overflow:hidden; min-height:50vw; }
    .hero-img-col img { width:100%; height:100%; object-fit:cover; filter:sepia(10%); }
    .hero-badge {
      position:absolute; bottom:2rem; left:2rem;
      background:#faf8f4; border-left:3px solid var(--terra);
      padding:1rem 1.4rem;
    }

    /* Producto card */
    .product-card { cursor:pointer; transition:transform .3s; }
    .product-card:hover { transform:translateY(-6px); }
    .product-img-wrap {
      aspect-ratio:3/4; overflow:hidden; position:relative; background:var(--sand);
    }
    .product-img-wrap img { width:100%; height:100%; object-fit:cover; transition:transform .5s; }
    .product-card:hover .product-img-wrap img { transform:scale(1.07); }
    .product-badge {
      position:absolute; top:.85rem; left:.85rem;
      background:var(--terra); color:#fff;
      font-size:.6rem; letter-spacing:.14em; text-transform:uppercase;
      padding:.25rem .65rem;
    }
    .product-name { font-family:'Cormorant Garamond',serif; font-size:1.2rem; font-weight:400; }
    .product-note { font-size:.8rem; color:#8a8480; }
    .product-price{ font-size:.9rem; color:var(--terra); }

    /* About numbers */
    .about-num-val {
      font-family:'Cormorant Garamond',serif;
      font-size:2.6rem; font-weight:300; color:var(--terra); display:block;
    }
    .about-num-lbl { font-size:.68rem; letter-spacing:.14em; text-transform:uppercase; opacity:.55; }

    /* Ingredient card */
    .ing-card {
      border:1px solid var(--sand) !important; border-radius:0 !important;
      background:#faf8f4; transition:border-color .25s, transform .25s;
    }
    .ing-card:hover { border-color:var(--terra) !important; transform:translateY(-4px); }
    .ing-icon { font-size:2.2rem; display:block; }

    /* Newsletter */
    .nl-input {
      background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
      color:#faf8f4; border-radius:0; font-family:'Jost',sans-serif; font-size:.88rem;
    }
    .nl-input::placeholder { color:rgba(255,255,255,.35); }
    .nl-input:focus { background:rgba(255,255,255,.13); border-color:var(--terra); box-shadow:none; color:#fff; }
    .btn-nl {
      background:var(--terra); border:none; color:#fff; border-radius:0;
      font-size:.72rem; letter-spacing:.18em; text-transform:uppercase;
      padding:.75rem 1.4rem; white-space:nowrap; transition:background .25s;
    }
    .btn-nl:hover { background:var(--terra-dk); color:#fff; }

    /* Footer */
    .footer-logo { font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:300; letter-spacing:.1em; }
    .footer-heading { font-size:.68rem; letter-spacing:.2em; text-transform:uppercase; opacity:.4; color:var(--sand); }
    .footer-link { color:#7a7470; text-decoration:none; font-size:.82rem; transition:color .2s; }
    .footer-link:hover { color:#f7f2eb; }

    /* Fade-up animation */
    @keyframes fadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
    .fade-up { animation:fadeUp .8s ease both; }
    .d1{animation-delay:.1s} .d2{animation-delay:.25s} .d3{animation-delay:.4s} .d4{animation-delay:.55s}
  </style>
</head>
<body>

<!-- ═══ NAVBAR ═══ -->
<nav class="navbar navbar-expand-lg fixed-top px-4">
  <a class="navbar-brand" href="#">Aromaris</a>
  <button class="navbar-toggler border-0" type="button"
          data-bs-toggle="collapse" data-bs-target="#mainNav">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="mainNav">
    <ul class="navbar-nav mx-auto gap-lg-3">
      <li class="nav-item"><a class="nav-link" href="#productos">Productos</a></li>
      <li class="nav-item"><a class="nav-link" href="#nosotros">Nosotros</a></li>
      <li class="nav-item"><a class="nav-link" href="#ingredientes">Ingredientes</a></li>
      <li class="nav-item"><a class="nav-link" href="login.php">Mi cuenta</a></li>
    </ul>
    <a href="#productos" class="btn btn-terra mt-2 mt-lg-0">Ver colección</a>
  </div>
</nav>

<!-- ═══ HERO ═══ -->
<section class="hero-section">
  <div class="row g-0 h-100">

    <div class="col-lg-6 bg-cream d-flex align-items-center">
      <div class="px-4 px-lg-5 py-5">
        <p class="section-tag fade-up d1 mb-3">Jabones artesanales · Desde 2018</p>
        <h1 class="font-display fw-light lh-1 mb-4 fade-up d2"
            style="font-size:clamp(2.8rem,5vw,5rem);">
          El ritual<br>de cuidarte<br><em class="text-terra">cada día</em>
        </h1>
        <p class="mb-4 fade-up d3"
           style="color:var(--muted); max-width:380px; line-height:1.85; font-size:.95rem;">
          Elaborados a mano con ingredientes naturales, esencias puras y aceites botánicos.
          Cada jabón es una experiencia sensorial única para tu piel y tu bienestar.
        </p>
        <div class="d-flex flex-wrap gap-3 fade-up d4">
          <a href="#productos" class="btn btn-terra">Explorar colección</a>
          <a href="#nosotros"  class="btn btn-outline-c">Nuestra historia</a>
        </div>
      </div>
    </div>

    <div class="col-lg-6 hero-img-col">
      <img src="https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=900&auto=format&fit=crop"
           alt="Jabones Aromaris"/>
      <div class="hero-badge">
        <p class="section-tag mb-0" style="font-size:.65rem;">100% natural</p>
        <span class="font-display" style="font-size:1.3rem;">Sin parabenos</span>
      </div>
    </div>

  </div>
</section>

<!-- ═══ BANDA ═══ -->
<div class="bg-dark-c py-3">
  <div class="container">
    <div class="row text-center g-2">
      <?php
      $feats = [
        ["bi-leaf",        "Ingredientes naturales"],
        ["bi-hand-index-thumb","Elaboración artesanal"],
        ["bi-box-seam",    "Envío en 24–48h"],
        ["bi-heart",       "Cruelty free"],
      ];
      foreach ($feats as $f): ?>
      <div class="col-6 col-md-3">
        <span style="font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; color:var(--sand);">
          <i class="bi <?= $f[0] ?> me-2"></i><?= $f[1] ?>
        </span>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</div>

<!-- ═══ PRODUCTOS ═══ -->
<section id="productos" class="py-5" style="padding-top:5rem !important; padding-bottom:5rem !important;">
  <div class="container">

    <div class="d-flex justify-content-between align-items-end mb-5">
      <div>
        <span class="section-tag d-block mb-2">Colección 2025</span>
        <h2 class="font-display fw-light mb-0" style="font-size:clamp(2rem,3.5vw,3rem);">Nuestros jabones</h2>
      </div>
      <a href="#" style="font-size:.73rem; letter-spacing:.15em; text-transform:uppercase;
         color:var(--dark); opacity:.55; border-bottom:1px solid; text-decoration:none;">
        Ver todos →
      </a>
    </div>

    <div class="row g-4">
      <?php
      $productos = [
        ["Rosa & Argán",      "Pétalos de rosa · Aceite de argán", "9,90 €","Más vendido","https://images.unsplash.com/photo-1602526432604-029a709e131b?w=400&auto=format&fit=crop"],
        ["Lavanda Provenzal", "Lavanda · Manteca de karité",        "8,50 €","",           "https://images.unsplash.com/photo-1619451819080-d8c7a97ce673?w=400&auto=format&fit=crop"],
        ["Citrus & Menta",    "Naranja dulce · Menta piperita",     "8,90 €","Nuevo",      "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=400&auto=format&fit=crop"],
        ["Vainilla & Coco",   "Vainilla natural · Aceite de coco",  "9,50 €","",           "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400&auto=format&fit=crop"],
      ];
      foreach ($productos as $p): ?>
      <div class="col-6 col-lg-3">
        <div class="product-card">
          <div class="product-img-wrap mb-3">
            <img src="<?= htmlspecialchars($p[4]) ?>" alt="<?= htmlspecialchars($p[0]) ?>"/>
            <?php if ($p[3]): ?>
              <span class="product-badge"><?= htmlspecialchars($p[3]) ?></span>
            <?php endif; ?>
          </div>
          <p class="product-name mb-1"><?= htmlspecialchars($p[0]) ?></p>
          <p class="product-note mb-1"><?= htmlspecialchars($p[1]) ?></p>
          <p class="product-price mb-0"><?= htmlspecialchars($p[2]) ?></p>
        </div>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ═══ ABOUT ═══ -->
<section id="nosotros" class="bg-cream">
  <div class="row g-0">

    <div class="col-lg-6" style="min-height:480px; overflow:hidden;">
      <img src="https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=800&auto=format&fit=crop"
           alt="Taller Aromaris"
           class="w-100 h-100" style="object-fit:cover; filter:sepia(8%);"/>
    </div>

    <div class="col-lg-6 d-flex align-items-center">
      <div class="p-4 p-lg-5">
        <span class="section-tag d-block mb-3">Nuestra historia</span>
        <h2 class="font-display fw-light mb-4" style="font-size:clamp(2rem,3vw,2.8rem);">
          Hechos con<br><em>amor y propósito</em>
        </h2>
        <p style="color:var(--muted); line-height:1.9; font-size:.95rem;">
          Aromaris nació en un pequeño obrador familiar con una sola convicción:
          que los productos de cuidado personal deben ser buenos para ti <em>y</em> para el planeta.
        </p>
        <p class="mt-3" style="color:var(--muted); line-height:1.9; font-size:.95rem;">
          Usamos aceites vegetales prensados en frío, esencias 100&nbsp;% puras y colorantes
          naturales. Cada pastilla pasa por un proceso de curado artesanal de cuatro semanas.
        </p>
        <div class="d-flex gap-4 mt-4">
          <div><span class="about-num-val">+6K</span><p class="about-num-lbl mb-0">Clientes felices</p></div>
          <div><span class="about-num-val">28</span><p class="about-num-lbl mb-0">Fragancias únicas</p></div>
          <div><span class="about-num-val">7</span><p class="about-num-lbl mb-0">Años de oficio</p></div>
        </div>
      </div>
    </div>

  </div>
</section>

<!-- ═══ INGREDIENTES ═══ -->
<section id="ingredientes" style="padding:5rem 0;">
  <div class="container">
    <div class="text-center mb-5">
      <span class="section-tag d-block mb-2">Lo que usamos</span>
      <h2 class="font-display fw-light" style="font-size:clamp(2rem,3.5vw,3rem);">Ingredientes estrella</h2>
    </div>
    <div class="row g-3">
      <?php
      $ings = [
        ["🫒","Aceite de oliva","Base nutritiva y suavizante. Rico en vitamina E y antioxidantes que protegen la piel."],
        ["🌹","Rosa mosqueta","Regenerador celular por excelencia. Aporta luminosidad y reduce marcas visibles."],
        ["🥥","Aceite de coco","Antibacteriano natural y emoliente profundo. Deja la piel sedosa y bien protegida."],
        ["💜","Lavanda francesa","Calmante y antiséptica. Perfecta para pieles sensibles y para relajar la mente."],
        ["🌿","Manteca de karité","Hidratación intensa de larga duración. Ideal para pieles secas y castigadas."],
        ["🍊","Aceites cítricos","Revitalizantes y purificantes. Aportan un aroma fresco y energizante único."],
      ];
      foreach ($ings as $i): ?>
      <div class="col-12 col-md-6 col-lg-4">
        <div class="ing-card card h-100 p-4 text-center">
          <span class="ing-icon mb-3"><?= $i[0] ?></span>
          <h3 class="font-display fw-normal mb-2" style="font-size:1.2rem;"><?= htmlspecialchars($i[1]) ?></h3>
          <p class="mb-0" style="font-size:.84rem; line-height:1.75; color:#7a7470;"><?= htmlspecialchars($i[2]) ?></p>
        </div>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ═══ NEWSLETTER ═══ -->
<section class="bg-dark-c text-white text-center" style="padding:5rem 1rem;">
  <div class="container">
    <span class="section-tag d-block mb-3" style="color:var(--sand); opacity:.6;">Novedades &amp; ofertas</span>
    <h2 class="font-display fw-light mb-3" style="font-size:clamp(2rem,3.5vw,3rem);">
      Únete a la comunidad<br><em>Aromaris</em>
    </h2>
    <p class="mx-auto mb-4" style="max-width:400px; line-height:1.8; font-size:.9rem; color:#a09890;">
      Suscríbete y recibe un 10&nbsp;% de descuento en tu primer pedido, además de acceso anticipado
      a nuestras nuevas colecciones.
    </p>
    <form class="d-flex justify-content-center mx-auto" style="max-width:420px;" action="#" method="post">
      <input type="email" name="email" placeholder="tu@email.com" required
             class="form-control nl-input rounded-0"/>
      <button type="submit" class="btn btn-nl">Suscribirme</button>
    </form>
  </div>
</section>

<!-- ═══ FOOTER ═══ -->
<footer style="background:#1e1b18; padding:3.5rem 0 2rem;">
  <div class="container">
    <div class="row g-4 mb-4">

      <div class="col-12 col-md-4">
        <span class="footer-logo d-block mb-3" style="color:var(--cream);">Aromaris</span>
        <p style="color:#7a7470; font-size:.82rem; line-height:1.8; max-width:240px;">
          Jabones artesanales elaborados con ingredientes naturales y mucho cuidado desde 2018.
        </p>
      </div>

      <?php
      $fcols = [
        "Tienda"      => ["Todos los productos","Novedades","Packs regalo","Ofertas"],
        "Información" => ["Sobre nosotros","Ingredientes","Sostenibilidad","Blog"],
        "Ayuda"       => ["Envíos y devoluciones","Preguntas frecuentes","Contacto","Mi cuenta"],
      ];
      foreach ($fcols as $title => $links): ?>
      <div class="col-6 col-md-2 col-lg-2">
        <h4 class="footer-heading mb-3"><?= $title ?></h4>
        <ul class="list-unstyled mb-0">
          <?php foreach ($links as $l): ?>
          <li class="mb-2"><a href="#" class="footer-link"><?= htmlspecialchars($l) ?></a></li>
          <?php endforeach; ?>
        </ul>
      </div>
      <?php endforeach; ?>
    </div>

    <hr style="border-color:rgba(255,255,255,.07);">
    <div class="d-flex flex-column flex-md-row justify-content-between align-items-center pt-2 gap-2"
         style="font-size:.72rem; color:#4a4440;">
      <span>© <?= date('Y') ?> Aromaris. Todos los derechos reservados.</span>
      <span>Hecho con 🌿 y cuidado artesanal</span>
    </div>
  </div>
</footer>

<!-- Bootstrap 5 JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>