<?php

define('DB_HOST', '10.20.40.11');
define('DB_NAME', 'aromaris_db');   // nombre de tu BD
define('DB_USER', 'antonio');    // usuario MariaDB
define('DB_PASS', '123456789'); // contraseña MariaDB
define('DB_PORT', '3306');

function conectar(): ?PDO {
    try {
        $dsn = "mysql:host=" . DB_HOST
             . ";port=" . DB_PORT
             . ";dbname=" . DB_NAME
             . ";charset=utf8mb4";

        return new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
    } catch (PDOException $e) {
        error_log("Error DB: " . $e->getMessage());
        return null;
    }
}

// ── Buscar usuario por email ────────────────────────────
function buscarUsuario(PDO $pdo, string $email): array|false {
    $stmt = $pdo->prepare(
        "SELECT id, email, password FROM usuarios WHERE email = ? LIMIT 1"
    );
    $stmt->execute([$email]);
    return $stmt->fetch();
}

// ── Registrar nuevo usuario ─────────────────────────────
function registrarUsuario(PDO $pdo, string $email, string $password): bool {
    try {
        $hash = password_hash($password, PASSWORD_BCRYPT);
        $stmt = $pdo->prepare(
            "INSERT INTO usuarios (email, password) VALUES (?, ?)"
        );
        return $stmt->execute([$email, $hash]);
    } catch (PDOException $e) {
        error_log("Error al registrar: " . $e->getMessage());
        return false;
    }
}
