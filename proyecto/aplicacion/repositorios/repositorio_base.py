"""Repositorio base con operaciones comunes de persistencia."""

from ..extenciones import base_de_datos


class RepositorioBase:
    """Encapsula las operaciones CRUD elementales sobre un modelo.

    Los repositorios concretos heredan de esta clase y agregan consultas
    específicas. Ninguna capa superior ejecuta SQL directamente.
    """

    modelo = None

    @property
    def sesion(self):
        """Sesión de SQLAlchemy asociada al contexto actual de la aplicación."""

        # `base_de_datos.session` es una sesión con alcance de contexto: Flask la
        # crea al iniciar la petición y la elimina al finalizarla.
        return base_de_datos.session

    def obtener_por_id(self, identificador: int):
        """Busca una entidad por su clave primaria; devuelve `None` si no existe."""

        # `Session.get` consulta primero el mapa de identidad antes de ir a la base.
        return self.sesion.get(self.modelo, identificador)

    def agregar(self, entidad):
        """Marca una entidad nueva para ser insertada en la próxima confirmación."""

        self.sesion.add(entidad)
        return entidad

    def agregar_varios(self, entidades) -> None:
        """Marca una colección de entidades nuevas para su inserción."""

        self.sesion.add_all(entidades)

    def eliminar(self, entidad) -> None:
        """Marca una entidad existente para ser eliminada."""

        self.sesion.delete(entidad)

    def confirmar_cambios(self) -> None:
        """Confirma la transacción actual de la sesión."""

        # `Session.commit` vuelca los cambios pendientes y finaliza la transacción.
        self.sesion.commit()

    def listar_todos(self):
        """Devuelve todas las entidades del modelo ordenadas por identificador."""

        from sqlalchemy import select

        # `select` construye una consulta tipada; `scalars` extrae las entidades
        # del resultado y `all` materializa la lista.
        return self.sesion.execute(select(self.modelo).order_by(self.modelo.id)).scalars().all()
