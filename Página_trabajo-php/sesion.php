<?php

session_start();
require_once 'database.php';

if (empty($_SESSION['csrf_token']))
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));

if (isset($_SESSION['usuario_id'])) {
    header('Location: mi-cuenta.php');
    exit;
}

$error   = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $accion   =      $_POST['accion']   ?? 'login';
    $email    = trim($_POST['email']    ?? '');
    $password =      $_POST['password'] ?? '';

    // Verificar CSRF
    if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'] ?? '')) {
        $error = 'Solicitud inválida. Inténtalo de nuevo.';

    } elseif (!$email || !$password) {
        $error = 'Por favor, completa todos los campos.';

    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'El formato del correo no es válido.';

    } else {
        $pdo = conectar(); // función de db.php

        if (!$pdo) {
            $error = 'No se pudo conectar con la base de datos.';

        } elseif ($accion === 'registro') {
            $existe = buscarUsuario($pdo, $email);
            if ($existe) {
                $error = 'Ese correo ya está registrado.';
            } elseif (registrarUsuario($pdo, $email, $password)) {
                $success = 'Cuenta creada correctamente. Ya puedes iniciar sesión.';
            } else {
                $error = 'No se pudo crear la cuenta. Inténtalo más tarde.';
            }

        } else {
            // ── LOGIN: busca usuario y verifica contraseña ──
            $usuario = buscarUsuario($pdo, $email); // función de db.php

            if ($usuario && password_verify($password, $usuario['password'])) {
                session_regenerate_id(true);
                $_SESSION['usuario_id']    = $usuario['id'];
                $_SESSION['usuario_email'] = $usuario['email'];
                header('Location: mi-cuenta.php');
                exit;
            } else {
                $error = 'Correo electrónico o contraseña incorrectos.';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Iniciar sesión — Aromaris</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;1,300&family=Jost:wght@300;400&display=swap" rel="stylesheet"/>
  <style>
    body { font-family: 'Jost', sans-serif; font-weight: 300; }
    .font-display { font-family: 'Cormorant Garamond', serif; }
  </style>
</head>
<body class="bg-light min-vh-100 d-flex align-items-center justify-content-center">

  <div class="card border-0 shadow-sm rounded-0 p-4 p-md-5" style="width:100%; max-width:420px;">

    <!-- Logo -->
    <div class="text-center mb-4">
      <a href="index.php" class="font-display fs-2 fw-light text-dark text-decoration-none">Aromaris</a>
      <p class="text-muted small mt-1 mb-0">Accede o crea tu cuenta</p>
    </div>

    <!-- Tabs login / registro -->
    <ul class="nav nav-tabs mb-4 rounded-0" id="authTabs">
      <li class="nav-item w-50 text-center">
        <a class="nav-link rounded-0 <?= (($_POST['accion'] ?? '') !== 'registro') ? 'active' : '' ?>"
           href="login.php">Iniciar sesión</a>
      </li>
      <li class="nav-item w-50 text-center">
        <a class="nav-link rounded-0 <?= (($_POST['accion'] ?? '') === 'registro') ? 'active' : '' ?>"
           href="?registro=1">Crear cuenta</a>
      </li>
    </ul>

    <!-- Error / Éxito -->
    <?php if ($error): ?>
    <div class="alert alert-danger rounded-0 border-0 border-start border-danger border-3 small">
      <?= htmlspecialchars($error) ?>
    </div>
    <?php endif; ?>

    <?php if ($success): ?>
    <div class="alert alert-success rounded-0 border-0 border-start border-success border-3 small">
      <?= htmlspecialchars($success) ?>
    </div>
    <?php endif; ?>

    <!-- Formulario -->
    <form action="login.php" method="post">
      <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
      <!-- 'accion' decide si es login o registro -->
      <input type="hidden" name="accion"
             value="<?= isset($_GET['registro']) ? 'registro' : 'login' ?>">

      <div class="mb-3">
        <label for="email" class="form-label small text-uppercase text-muted">Correo electrónico</label>
        <input type="email" id="email" name="email" class="form-control rounded-0"
               placeholder="tu@email.com"
               value="<?= htmlspecialchars($_POST['email'] ?? '') ?>"
               required/>
      </div>

      <div class="mb-2">
        <label for="password" class="form-label small text-uppercase text-muted">Contraseña</label>
        <input type="password" id="password" name="password"
               class="form-control rounded-0" placeholder="••••••••" required/>
      </div>

      <?php if (!isset($_GET['registro'])): ?>
      <div class="text-end mb-3">
        <a href="recuperar-contrasena.php" class="text-danger small text-decoration-none">
          ¿Olvidaste tu contraseña?
        </a>
      </div>
      <?php else: ?>
      <div class="mb-3"></div>
      <?php endif; ?>

      <button type="submit" class="btn btn-danger rounded-0 w-100 py-2 small text-uppercase">
        <?= isset($_GET['registro']) ? 'Crear cuenta' : 'Iniciar sesión' ?>
      </button>
    </form>

    <div class="text-center mt-4">
      <a href="index.php" class="text-muted text-decoration-none small">← Volver a la tienda</a>
    </div>

  </div>

</body>
</html><?php
session_start();

if (empty($_SESSION['csrf_token']))
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'] ?? '')) {
        $error = 'Solicitud inválida. Inténtalo de nuevo.';
    } else {
        $email    = trim($_POST['email']    ?? '');
        $password =      $_POST['password'] ?? '';

        if (!$email || !$password) {
            $error = 'Por favor, completa todos los campos.';
        } else {
            // Aquí iría la validación con la base de datos
            // $error = 'Correo o contraseña incorrectos.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Iniciar sesión — Aromaris</title>

  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;1,300&family=Jost:wght@300;400&display=swap" rel="stylesheet"/>

  <style>
    :root {
      --terra: #c8735a;
      --dark:  #2e2a26;
      --sand:  #e8ddd0;
    }
    body {
      font-family: 'Jost', sans-serif;
      font-weight: 300;
      background: #f7f2eb;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      border: none;
      border-radius: 0;
      box-shadow: 0 8px 40px rgba(0,0,0,.08);
      width: 100%;
      max-width: 400px;
      padding: 2.8rem 2.5rem;
      background: #faf8f4;
    }
    .brand {
      font-family: 'Cormorant Garamond', serif;
      font-size: 2.2rem;
      font-weight: 300;
      letter-spacing: .1em;
      color: var(--dark);
    }
    .form-label {
      font-size: .7rem;
      letter-spacing: .18em;
      text-transform: uppercase;
      color: var(--dark);
      opacity: .6;
    }
    .form-control {
      border: 1.5px solid var(--sand);
      border-radius: 0;
      background: #faf8f4;
      font-family: 'Jost', sans-serif;
      color: var(--dark);
      padding: .7rem 1rem;
    }
    .form-control:focus {
      border-color: var(--terra);
      box-shadow: none;
      background: #faf8f4;
    }
    .btn-login {
      background: var(--terra);
      color: #fff;
      border: none;
      border-radius: 0;
      width: 100%;
      padding: .8rem;
      font-size: .75rem;
      letter-spacing: .18em;
      text-transform: uppercase;
      transition: background .2s;
    }
    .btn-login:hover { background: #b56249; color: #fff; }
    .link-terra { color: var(--terra); font-size: .8rem; text-decoration: none; }
    .link-terra:hover { text-decoration: underline; }
    .divider { border-color: var(--sand); }
    .btn-register {
      width: 100%;
      border: 1.5px solid var(--dark);
      border-radius: 0;
      background: transparent;
      color: var(--dark);
      font-size: .75rem;
      letter-spacing: .18em;
      text-transform: uppercase;
      padding: .75rem;
      transition: background .2s, color .2s;
      text-decoration: none;
      display: block;
      text-align: center;
    }
    .btn-register:hover { background: var(--dark); color: #fff; }
    .alert {
      border-radius: 0;
      border: none;
      border-left: 3px solid var(--terra);
      background: #fdf0ed;
      color: #9a4a36;
      font-size: .84rem;
    }
  </style>
</head>
<body>

  <div class="card">

    <div class="text-center mb-4">
      <a href="index.php" class="brand text-decoration-none">Aromaris</a>
      <p class="mt-1 mb-0" style="font-size:.82rem; color:#8a8480;">Inicia sesión en tu cuenta</p>
    </div>

    <?php if ($error): ?>
    <div class="alert mb-3"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <form action="login.php" method="post">
      <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">

      <div class="mb-3">
        <label for="email" class="form-label">Correo electrónico</label>
        <input type="email" id="email" name="email" class="form-control"
               placeholder="tu@email.com"
               value="<?= htmlspecialchars($_POST['email'] ?? '') ?>"
               required/>
      </div>

      <div class="mb-2">
        <label for="password" class="form-label">Contraseña</label>
        <input type="password" id="password" name="password"
               class="form-control" placeholder="••••••••" required/>
      </div>

      <div class="text-end mb-4">
        <a href="recuperar-contrasena.php" class="link-terra">¿Olvidaste tu contraseña?</a>
      </div>

      <button type="submit" class="btn btn-login mb-3">Iniciar sesión</button>
    </form>

    <hr class="divider my-3">

    <a href="registro.php" class="btn-register">Crear una cuenta</a>

  </div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
