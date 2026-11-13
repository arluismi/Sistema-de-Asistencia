"""Gestión segura de contraseñas mediante Werkzeug."""

from werkzeug.security import check_password_hash, generate_password_hash


def generar_hash_contrasena(contrasena: str) -> str:
    """Genera un hash irreversible con sal aleatoria para almacenar la contraseña.

    `generate_password_hash` de Werkzeug aplica un algoritmo de derivación con
    sal incorporada; nunca se guarda la contraseña original.
    """

    return generate_password_hash(contrasena)


def verificar_contrasena(contrasena: str, hash_almacenado: str) -> bool:
    """Compara la contraseña recibida con el hash almacenado.

    `check_password_hash` reconstruye el hash con la sal guardada y compara en
    tiempo constante para reducir riesgos de ataques por temporización.
    """

    return check_password_hash(hash_almacenado, contrasena)
