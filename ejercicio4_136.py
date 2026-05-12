# =============================================================================
# UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA (UNAD)
# CURSO: PROGRAMACIÓN (CÓDIGO 213023)
# FASE 4: PRÁCTICAS SIMULADAS - MANEJO DE EXCEPCIONES
# GRUPO: [136]
# ESTUDIANTES: [JUAN DAVID BARRERO RUEDA - JOHAN SEBASTIAN BLANCO MEJIA - KARINA ANDREA RUEDA TORRES - ANDRES DAVID SANCHEZ FONSECA]
# FECHA: [11 DE MAYO DE 2026]
# PROYECTO: Sistema Integral de Gestión - Software FJ
# =============================================================================

"""
MÓDULO PRINCIPAL: Sistema de Gestión con Manejo Robusto de Excepciones

PROPÓSITO:
- Implementar arquitectura orientada a objetos para gestión de clientes, 
  servicios y reservas de la empresa Software FJ
- Demostrar manejo avanzado de excepciones manteniendo la aplicación estable
- Registrar todos los eventos en archivo de logs sin usar base de datos

PRINCIPIOS POO APLICADOS:
- ABSTRACCIÓN: Clases BaseEntity y Service como contratos base
- HERENCIA: Customer, RoomReservation, EquipmentRental, ConsultingService
- POLIMORFISMO: Métodos get_description() y calculate_cost() con comportamientos distintos
- ENCAPSULAMIENTO: Atributos privados con validación en propiedades
- MANEJO DE EXCEPCIONES: try/except/else/finally + personalizadas + encadenamiento
"""

# -----------------------------------------------------------------------------
# IMPORTACIÓN DE MÓDULOS Y LIBRERÍAS
# -----------------------------------------------------------------------------

import tkinter as tk                          # Módulo para interfaz gráfica (GUI)
from tkinter import messagebox, ttk           # Componentes adicionales para GUI
import logging                                # Módulo para registro de eventos en logs
import re                                     # Módulo para expresiones regulares (validación de email)
from abc import ABC, abstractmethod           # Módulo para clases y métodos abstractos (POO)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DEL SISTEMA DE LOGS
# -----------------------------------------------------------------------------

# Configura el registro automático de eventos en archivo de texto
# FORMATO: [fecha-hora] - NIVEL - mensaje
# NIVELES: DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(
    filename="fj_management_v2.log",           # Nombre del archivo de logs
    level=logging.INFO,                         # Nivel mínimo a registrar
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato de cada línea
    encoding="utf-8"                            # Soporte para caracteres especiales (ñ, tildes)
)

# Registrar inicio del sistema en logs
logging.info("=== SISTEMA SOFTWARE FJ INICIADO ===")


# =============================================================================
# MÓDULO 1: EXCEPCIONES PERSONALIZADAS Y ENCADENAMIENTO
# =============================================================================

class FJError(Exception):
    """
    CLASE: Excepción base para todo el sistema Software FJ.
    
    PROPÓSITO:
    - Sirve como clase padre para todas las excepciones personalizadas
    - Permite capturar cualquier error del sistema con un solo 'except FJError'
    - Facilita el registro consistente de errores en logs
    """
    def __init__(self, mensaje, codigo_error=500):
        """
        CONSTRUCTOR: Inicializa la excepción con mensaje y código.
        
        PARÁMETROS:
            mensaje (str): Descripción legible del error para el usuario
            codigo_error (int, opcional): Código numérico para identificación técnica
        """
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        super().__init__(self.mensaje)
    
    def __str__(self):
        """RETORNA: Representación en string con formato [Código] Mensaje"""
        return f"[Error {self.codigo_error}] {self.mensaje}"


class ValidationError(FJError):
    """
    EXCEPCIÓN: Se lanza cuando los datos de entrada no cumplen validaciones.
    
    CASOS DE USO:
    - Nombre de cliente vacío o con formato inválido
    - Email con estructura incorrecta
    - Cantidad negativa o cero en reservas
    - Edad menor a 18 años para clientes
    """
    def __init__(self, mensaje, campo_afectado=None):
        """
        CONSTRUCTOR: Inicializa error de validación.
        
        PARÁMETROS:
            mensaje (str): Descripción del error de validación
            campo_afectado (str, opcional): Nombre del campo que falló la validación
        """
        super().__init__(mensaje, codigo_error=1001)
        self.campo_afectado = campo_afectado  # Permite identificar qué campo validar


class ProcessingError(FJError):
    """
    EXCEPCIÓN: Se lanza cuando una operación de negocio falla durante el procesamiento.
    
    CASOS DE USO:
    - Confirmación de reserva con datos inconsistentes
    - Cálculo de costos con parámetros inválidos
    - Operaciones no permitidas según el estado del objeto
    
    PRINCIPIO: ENCADENAMIENTO DE EXCEPCIONES
    - Se usa 'raise ProcessingError(...) from causa_original'
    - Esto preserva el traceback completo para depuración
    """
    def __init__(self, mensaje, causa_original=None):
        """
        CONSTRUCTOR: Inicializa error de procesamiento con encadenamiento.
        
        PARÁMETROS:
            mensaje (str): Descripción del error de procesamiento
            causa_original (Exception, opcional): Excepción que originó este error
        """
        super().__init__(mensaje, codigo_error=2001)
        self.causa_original = causa_original


class ServiceNotFoundError(FJError):
    """
    EXCEPCIÓN: Se lanza cuando se solicita un servicio que no existe.
    
    CASOS DE USO:
    - Buscar servicio por tipo no registrado en el sistema
    - Intentar reservar un servicio eliminado o desactivado
    """
    def __init__(self, servicio_tipo):
        """
        CONSTRUCTOR: Inicializa error de servicio no encontrado.
        
        PARÁMETROS:
            servicio_tipo (str): Tipo o nombre del servicio que no se encontró
        """
        super().__init__(f"Servicio '{servicio_tipo}' no encontrado en el sistema", codigo_error=3001)
        self.servicio_tipo = servicio_tipo


# =============================================================================
# MÓDULO 2: CLASES DE ENTIDADES (ABSTRACCIÓN + ENCAPSULAMIENTO)
# =============================================================================

class BaseEntity(ABC):
    """
    CLASE ABSTRACTA: Representa una entidad genérica del sistema.
    
    PROPÓSITO:
    - Define contrato base con ID único para todas las entidades
    - Establece método abstracto __str__ para representación textual
    - No se puede instanciar directamente, solo mediante clases hijas
    
    PRINCIPIO POO: ABSTRACCIÓN + ENCAPSULAMIENTO
    """
    
    # Contador de clase para generar IDs únicos automáticamente
    _id_counter = 0
    
    def __init__(self):
        """
        CONSTRUCTOR: Asigna ID único y registra creación en logs.
        
        PROCESO:
        1. Incrementa contador global de IDs
        2. Asigna ID único a la nueva entidad
        3. Registra evento de creación en archivo de logs
        """
        BaseEntity._id_counter += 1
        self._entity_id = BaseEntity._id_counter
        logging.debug(f"Entidad creada con ID: {self._entity_id}")
    
    @property
    def entity_id(self):
        """
        GETTER: Obtiene el ID único de la entidad.
        
        RETURNS:
            int: Identificador único de solo lectura
        """
        return self._entity_id
    
    @abstractmethod
    def __str__(self):
        """
        MÉTODO ABSTRACTO: Retorna representación textual de la entidad.
        
        PROPÓSITO:
        - Cada clase hija debe definir su propia representación
        - Útil para logs, debugging y visualización en consola
        """
        pass


class Customer(BaseEntity):
    """
    CLASE DERIVADA: Representa un cliente del sistema Software FJ.
    
    ATRIBUTOS (ENCAPSULADOS):
        __name (str): Nombre completo del cliente (privado)
        __email (str): Correo electrónico validado (privado)
        __age (int): Edad del cliente, mínimo 18 años (privado)
        __active (bool): Estado de actividad del cliente (privado)
    
    VALIDACIONES ROBUSTAS:
        - Nombre: No vacío, mínimo 3 caracteres, solo letras y espacios
        - Email: Formato válido con expresión regular
        - Edad: Entre 18 y 120 años
        - ID: Generado automáticamente, único por sistema
    
    PRINCIPIO POO: HERENCIA + ENCAPSULAMIENTO + VALIDACIÓN
    """
    
    def __init__(self, name, customer_id=None, email=None, age=None):
        """
        CONSTRUCTOR: Inicializa un cliente con validaciones estrictas.
        
        PARÁMETROS:
            name (str): Nombre completo del cliente (obligatorio)
            customer_id (str, opcional): ID personalizado o generado
            email (str, opcional): Correo electrónico para contacto
            age (int, opcional): Edad del cliente para validación
        
        MANEJO DE EXCEPCIONES:
        - try/except: Captura errores de validación durante construcción
        - Registra errores en logs sin detener la aplicación
        """
        super().__init__()  # Llamar constructor de BaseEntity para ID único
        
        # Asignar ID personalizado si se proporciona, sino usar el generado
        if customer_id:
            self._entity_id = customer_id
        
        try:
            # VALIDACIÓN 1: Nombre (no vacío, formato correcto)
            if not name or not name.strip():
                raise ValidationError("El nombre del cliente es obligatorio", "name")
            if len(name.strip()) < 3:
                raise ValidationError("El nombre debe tener al menos 3 caracteres", "name")
            if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", name.strip()):
                raise ValidationError("El nombre solo puede contener letras y espacios", "name")
            self.__name = name.strip()
            
            # VALIDACIÓN 2: Email (formato válido si se proporciona)
            if email and not self._validate_email(email):
                raise ValidationError(f"Formato de email inválido: {email}", "email")
            self.__email = email.strip().lower() if email else None
            
            # VALIDACIÓN 3: Edad (rango permitido 18-120 si se proporciona)
            if age is not None:
                if not isinstance(age, int) or age < 18 or age > 120:
                    raise ValidationError("La edad debe estar entre 18 y 120 años", "age")
            self.__age = age
            
            # Estado inicial: cliente activo por defecto
            self.__active = True
            
            # Registrar creación exitosa en logs
            logging.info(f"Cliente creado: {self.__name} (ID: {self.entity_id})")
            
        except ValidationError as e:
            # Registrar error de validación con contexto
            logging.warning(f"Error al crear cliente: {e.mensaje} | Campo: {e.campo_afectado}")
            # Re-lanzar para que el llamador decida cómo manejar
            raise
    
    def _validate_email(self, email):
        """
        MÉTODO PRIVADO: Valida formato de email con expresión regular.
        
        PARÁMETROS:
            email (str): Dirección de correo a validar
        
        RETURNS:
            bool: True si el formato es válido, False si no
        
        PATRÓN REGEX:
            - Parte local: letras, números, puntos, guiones, +, %
            - @ símbolo obligatorio
            - Dominio: letras, números, puntos, guiones
            - TLD: mínimo 2 letras (com, org, co, etc.)
        """
        # Expresión regular para validación básica de email
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    # -------------------------------------------------------------------------
    # PROPIEDADES CON ENCAPSULAMIENTO (GETTERS)
    # -------------------------------------------------------------------------
    
    @property
    def name(self):
        """GETTER: Obtiene el nombre del cliente (solo lectura externa)."""
        return self.__name
    
    @property
    def email(self):
        """GETTER: Obtiene el email del cliente (solo lectura externa)."""
        return self.__email
    
    @property
    def age(self):
        """GETTER: Obtiene la edad del cliente (solo lectura externa)."""
        return self.__age
    
    @property
    def is_active(self):
        """GETTER: Obtiene el estado de actividad del cliente."""
        return self.__active
    
    def deactivate(self):
        """MÉTODO: Desactiva el cliente (ej: por cancelación de cuenta)."""
        self.__active = False
        logging.info(f"Cliente {self.entity_id} desactivado")
    
    # -------------------------------------------------------------------------
    # IMPLEMENTACIÓN DE MÉTODO ABSTRACTO
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """
        MÉTODO: Retorna representación textual del cliente.
        
        RETURNS:
            str: Formato "Customer: Nombre (ID: xxx)"
        
        USO: Logs, debugging, visualización en consola
        """
        estado = "ACTIVO" if self.__active else "INACTIVO"
        return f"Customer: {self.__name} (ID: {self.entity_id}) [{estado}]"


# =============================================================================
# MÓDULO 3: CLASES DE SERVICIOS (ABSTRACCIÓN + POLIMORFISMO + SOBRECARGA)
# =============================================================================

class Service(ABC):
    """
    CLASE ABSTRACTA: Representa un servicio genérico de Software FJ.
    
    PROPÓSITO:
    - Define interfaz común para todos los servicios del sistema
    - Establece métodos para cálculo de costos con parámetros opcionales
    - Permite tratamiento polimórfico de diferentes tipos de servicios
    
    ATRIBUTOS:
        name (str): Nombre descriptivo del servicio
        base_rate (float): Precio base por unidad/hora del servicio
    
    PRINCIPIO POO: ABSTRACCIÓN + POLIMORFISMO + SOBRECARGA SIMULADA
    """
    
    # Constantes de negocio aplicables a todos los servicios
    IVA_RATE = 0.19              # 19% de IVA (impuesto estándar)
    MAX_DISCOUNT = 0.30          # 30% máximo de descuento permitido
    
    def __init__(self, name, base_rate):
        """
        CONSTRUCTOR: Inicializa un servicio con nombre y precio base.
        
        PARÁMETROS:
            name (str): Nombre descriptivo del servicio
            base_rate (float): Precio base por unidad (debe ser > 0)
        
        VALIDACIONES:
            - base_rate debe ser positivo para evitar cálculos inválidos
        """
        if base_rate <= 0:
            raise ValidationError(f"El precio base debe ser mayor a cero: {base_rate}", "base_rate")
        
        self.name = name
        self.base_rate = base_rate
        logging.debug(f"Servicio creado: {name} - Precio base: ${base_rate}")
    
    @abstractmethod
    def get_description(self):
        """
        MÉTODO ABSTRACTO: Retorna descripción detallada del servicio.
        
        PROPÓSITO:
        - Cada servicio derivado define su propia descripción
        - Útil para visualización en UI y documentación
        
        RETURNS:
            str: Descripción textual del servicio
        """
        pass
    
    def validate_quantity(self, quantity):
        """
        MÉTODO: Valida que la cantidad sea un número positivo.
        
        PARÁMETROS:
            quantity (int/float): Cantidad de unidades/horas a validar
        
        RAISES:
            ValidationError: Si quantity <= 0
        
        NOTA: Método reusable por todos los servicios derivados
        """
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValidationError(
                f"Cantidad inválida para '{self.name}': debe ser mayor a cero",
                "quantity"
            )
    
    def calculate_cost(self, quantity, tax=IVA_RATE, discount=0.0):
        """
        MÉTODO CON SOBRECARGA SIMULADA: Calcula costo total del servicio.
        
        PARÁMETROS:
            quantity (int/float): Cantidad de unidades/horas (obligatorio)
            tax (float, opcional): Porcentaje de impuestos (default: 0.19 = 19%)
            discount (float, opcional): Porcentaje de descuento (default: 0.0 = 0%)
        
        FÓRMULA:
            subtotal = quantity × base_rate
            total = (subtotal × (1 + tax)) - (subtotal × discount)
        
        RETURNS:
            float: Costo total redondeado a 2 decimales
        
        PRINCIPIO POO: SOBRECARGA SIMULADA EN PYTHON
        - Python no soporta sobrecarga real (mismo nombre, diferentes parámetros)
        - Se simula usando parámetros con valores por defecto
        - Permite llamar con diferentes combinaciones de argumentos
        
        EJEMPLOS DE USO:
            servicio.calculate_cost(5)                    # tax=0.19, discount=0.0
            servicio.calculate_cost(5, tax=0.0)           # Sin impuestos
            servicio.calculate_cost(5, discount=0.15)     # 15% de descuento
            servicio.calculate_cost(5, tax=0.0, discount=0.10)  # Sin impuestos + 10% descuento
        """
        try:
            # Validar cantidad antes de calcular
            self.validate_quantity(quantity)
            
            # Validar rangos de tax y discount
            if not (0 <= tax <= 1):
                raise ValidationError(f"El impuesto debe estar entre 0 y 1: {tax}", "tax")
            if not (0 <= discount <= self.MAX_DISCOUNT):
                raise ValidationError(
                    f"El descuento debe estar entre 0 y {self.MAX_DISCOUNT}: {discount}",
                    "discount"
                )
            
            # Calcular subtotal (cantidad × precio base)
            subtotal = quantity * self.base_rate
            
            # Aplicar impuestos: subtotal × (1 + tax)
            con_impuestos = subtotal * (1 + tax)
            
            # Aplicar descuento: con_impuestos - (subtotal × discount)
            # Nota: El descuento se aplica sobre el subtotal, no sobre el total con impuestos
            total = con_impuestos - (subtotal * discount)
            
            # Registrar cálculo exitoso en logs
            logging.debug(
                f"Cálculo de costo: {self.name} | Qty: {quantity} | "
                f"Subtotal: ${subtotal:.2f} | Total: ${total:.2f}"
            )
            
            # Retornar valor redondeado a 2 decimales (formato moneda)
            return round(total, 2)
            
        except ValidationError as e:
            # Registrar error de validación en cálculo
            logging.error(f"Error al calcular costo: {e.mensaje} | Servicio: {self.name}")
            raise
        
        except Exception as e:
            # Capturar cualquier error inesperado durante cálculo
            logging.critical(
                f"Error crítico en calculate_cost: {type(e).__name__}: {e} | "
                f"Servicio: {self.name} | Qty: {quantity}",
                exc_info=True  # Incluir traceback completo para debugging
            )
            raise ProcessingError(f"Error inesperado al calcular costo: {e}", causa_original=e) from e


# -----------------------------------------------------------------------------
# SERVICIO 1: RESERVA DE SALAS DE REUNIONES
# -----------------------------------------------------------------------------

class RoomReservation(Service):
    """
    CLASE DERIVADA: Servicio de reserva de salas con equipos audiovisuales.
    
    CARACTERÍSTICAS:
    - Incluye proyector, pantalla, micrófono y conexión internet
    - Precio base por hora de uso
    - Capacidad estándar de 10-50 personas
    
    PRINCIPIO POO: HERENCIA + POLIMORFISMO
    """
    
    def get_description(self):
        """
        IMPLEMENTACIÓN POLIMÓRFICA: Descripción específica para sala de reuniones.
        
        RETURNS:
            str: Descripción detallada del servicio de sala
        """
        return "Meeting room with audiovisual equipment (projector, screen, microphone, WiFi)."
    
    def calculate_cost(self, hours, tax=Service.IVA_RATE, discount=0.0, include_setup=False):
        """
        SOBRECARGA EXTENDIDA: Calcula costo con parámetro adicional para salas.
        
        PARÁMETROS ADICIONALES:
            include_setup (bool, opcional): Incluir costo de configuración inicial (default: False)
        
        FÓRMULA EXTENDIDA:
            Si include_setup=True: total = costo_base + $25 (configuración)
        
        RETURNS:
            float: Costo total con configuración opcional
        """
        # Calcular costo base usando método padre
        base_cost = super().calculate_cost(hours, tax, discount)
        
        # Agregar costo de configuración si se solicita
        if include_setup:
            setup_fee = 25.0  # Costo fijo de configuración de equipos
            base_cost += setup_fee
            logging.debug(f"Setup fee added: ${setup_fee} | New total: ${base_cost:.2f}")
        
        return round(base_cost, 2)


# -----------------------------------------------------------------------------
# SERVICIO 2: ALQUILER DE EQUIPOS TECNOLÓGICOS
# -----------------------------------------------------------------------------

class EquipmentRental(Service):
    """
    CLASE DERIVADA: Servicio de alquiler de equipos de cómputo y oficina.
    
    CARACTERÍSTICAS:
    - Equipos de alta gama: laptops, proyectores, impresoras
    - Precio base por día de alquiler
    - Incluye soporte técnico básico
    
    PRINCIPIO POO: HERENCIA + POLIMORFISMO
    """
    
    def get_description(self):
        """
        IMPLEMENTACIÓN POLIMÓRFICA: Descripción específica para alquiler de equipos.
        
        RETURNS:
            str: Descripción detallada del servicio de equipos
        """
        return "High-end computing or office equipment rental (laptops, projectors, printers) with basic technical support."
    
    def calculate_cost(self, days, tax=Service.IVA_RATE, discount=0.0, with_insurance=False):
        """
        SOBRECARGA EXTENDIDA: Calcula costo con seguro opcional para equipos.
        
        PARÁMETROS ADICIONALES:
            with_insurance (bool, opcional): Incluir seguro contra daños (default: False)
        
        FÓRMULA EXTENDIDA:
            Si with_insurance=True: total = costo_base + (base_rate × 0.10)
            (10% del precio base como prima de seguro por día)
        
        RETURNS:
            float: Costo total con seguro opcional
        """
        # Calcular costo base usando método padre
        base_cost = super().calculate_cost(days, tax, discount)
        
        # Agregar costo de seguro si se solicita
        if with_insurance:
            insurance_fee = self.base_rate * 0.10 * days  # 10% del precio base por día
            base_cost += insurance_fee
            logging.debug(f"Insurance fee added: ${insurance_fee:.2f} | New total: ${base_cost:.2f}")
        
        return round(base_cost, 2)


# -----------------------------------------------------------------------------
# SERVICIO 3: ASESORÍAS ESPECIALIZADAS (NUEVO - REQUISITO CUMPLIDO)
# -----------------------------------------------------------------------------

class ConsultingService(Service):
    """
    CLASE DERIVADA: Servicio de asesorías especializadas en tecnología.
    
    CARACTERÍSTICAS:
    - Niveles de consultor: junior, senior, expert (con multiplicadores de costo)
    - Modalidades: presencial o remota
    - Precio base por hora, ajustado según nivel del consultor
    
    PRINCIPIO POO: HERENCIA + POLIMORFISMO + SOBRECARGA AVANZADA
    """
    
    # Multiplicadores de costo según nivel del consultor
    LEVEL_MULTIPLIERS = {
        "junior": 1.0,    # Precio base sin multiplicador
        "senior": 1.5,    # 50% adicional sobre precio base
        "expert": 2.0     # 100% adicional (doble) sobre precio base
    }
    
    def __init__(self, name, base_rate, consultant_level="junior", modality="remote"):
        """
        CONSTRUCTOR: Inicializa servicio de asesoría con nivel y modalidad.
        
        PARÁMETROS:
            name (str): Nombre/título de la asesoría
            base_rate (float): Precio base por hora
            consultant_level (str): Nivel del consultor (junior/senior/expert)
            modality (str): Modalidad de la asesoría (presencial/remota)
        
        VALIDACIONES:
            - consultant_level debe estar en LEVEL_MULTIPLIERS
            - modality debe ser "presencial" o "remota"
        """
        # Validar nivel del consultor antes de inicializar
        if consultant_level not in self.LEVEL_MULTIPLIERS:
            raise ValidationError(
                f"Nivel de consultor inválido: '{consultant_level}'. "
                f"Opciones válidas: {list(self.LEVEL_MULTIPLIERS.keys())}",
                "consultant_level"
            )
        
        # Validar modalidad antes de inicializar
        if modality not in ["presencial", "remota"]:
            raise ValidationError(
                f"Modalidad inválida: '{modality}'. Opciones: 'presencial' o 'remota'",
                "modality"
            )
        
        # Llamar constructor padre con nombre y precio base
        super().__init__(name, base_rate)
        
        # Asignar atributos específicos de asesoría
        self.consultant_level = consultant_level.lower()
        self.modality = modality.lower()
        
        logging.info(
            f"Consulting service created: {name} | Level: {consultant_level} | "
            f"Modality: {modality} | Base rate: ${base_rate}/hour"
        )
    
    def get_description(self):
        """
        IMPLEMENTACIÓN POLIMÓRFICA: Descripción específica para asesorías.
        
        RETURNS:
            str: Descripción detallada con nivel y modalidad del consultor
        """
        # Mapeo de niveles a descripciones amigables
        level_descriptions = {
            "junior": "Junior Consultant",
            "senior": "Senior Expert",
            "expert": "Lead Specialist"
        }
        
        # Mapeo de modalidades a descripciones amigables
        modality_descriptions = {
            "presencial": "On-site",
            "remota": "Remote"
        }
        
        # Construir descripción completa
        level_desc = level_descriptions.get(self.consultant_level, "Consultant")
        modality_desc = modality_descriptions.get(self.modality, "Service")
        
        return f"{level_desc} - {self.name} ({modality_desc} consultation)"
    
    def calculate_cost(self, hours, tax=Service.IVA_RATE, discount=0.0, include_travel=False):
        """
        SOBRECARGA AVANZADA: Calcula costo de asesoría con multiplicador de nivel.
        
        PARÁMETROS ADICIONALES:
            include_travel (bool, opcional): Incluir costo de viaje para modalidad presencial
        
        FÓRMULA:
            1. Aplicar multiplicador según nivel: base_rate × LEVEL_MULTIPLIERS[nivel]
            2. Calcular subtotal: horas × precio_ajustado
            3. Aplicar impuestos y descuento
            4. Si include_travel=True y modalidad=presencial: agregar $50 de viaje
        
        RETURNS:
            float: Costo total con ajustes por nivel y viaje opcional
        """
        try:
            # Validar cantidad de horas
            self.validate_quantity(hours)
            
            # Obtener multiplicador según nivel del consultor
            multiplier = self.LEVEL_MULTIPLIERS.get(self.consultant_level, 1.0)
            
            # Calcular precio ajustado por nivel
            adjusted_rate = self.base_rate * multiplier
            
            # Calcular subtotal con precio ajustado
            subtotal = hours * adjusted_rate
            
            # Aplicar impuestos: subtotal × (1 + tax)
            con_impuestos = subtotal * (1 + tax)
            
            # Aplicar descuento sobre el subtotal (no sobre el total con impuestos)
            total = con_impuestos - (subtotal * discount)
            
            # Agregar costo de viaje si aplica (solo para modalidad presencial)
            if include_travel and self.modality == "presencial":
                travel_fee = 50.0  # Costo fijo de viaje para asesoría presencial
                total += travel_fee
                logging.debug(f"Travel fee added: ${travel_fee} | New total: ${total:.2f}")
            elif include_travel and self.modality == "remota":
                # Advertencia: no se cobra viaje para modalidad remota
                logging.warning(
                    f"Travel fee requested for remote consultation '{self.name}' - ignored"
                )
            
            # Registrar cálculo exitoso con detalles
            logging.debug(
                f"Consulting cost calculated: {self.name} | Level: {self.consultant_level} | "
                f"Hours: {hours} | Adjusted rate: ${adjusted_rate:.2f}/h | Total: ${total:.2f}"
            )
            
            return round(total, 2)
            
        except ValidationError as e:
            logging.error(f"Validation error in consulting cost: {e.mensaje}")
            raise
        
        except Exception as e:
            logging.critical(
                f"Critical error in ConsultingService.calculate_cost: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise ProcessingError(f"Error calculating consulting cost: {e}", causa_original=e) from e


# =============================================================================
# MÓDULO 4: CLASE RESERVA (INTEGRACIÓN + MANEJO DE EXCEPCIONES AVANZADO)
# =============================================================================

class Reservation:
    """
    CLASE: Representa una reserva que integra cliente, servicio y estado.
    
    ATRIBUTOS:
        customer (Customer): Cliente que realiza la reserva
        service (Service): Servicio reservado (polimórfico)
        quantity (int): Cantidad de unidades/horas/días
        status (str): Estado de la reserva (Pending/Confirmed/Cancelled)
        total_cost (float): Costo total calculado al confirmar
    
    ESTADOS VÁLIDOS:
        - "Pending": Reserva creada pero no confirmada
        - "Confirmed": Reserva confirmada y lista para usar
        - "Cancelled": Reserva cancelada (no modificable)
    
    PRINCIPIO POO: COMPOSICIÓN + MANEJO AVANZADO DE EXCEPCIONES
    """
    
    # Estados permitidos para reservas
    STATUSES = ["Pending", "Confirmed", "Cancelled"]
    
    def __init__(self, customer, service, quantity):
        """
        CONSTRUCTOR: Inicializa una nueva reserva.
        
        PARÁMETROS:
            customer (Customer): Objeto cliente válido
            service (Service): Objeto servicio a reservar
            quantity (int): Cantidad positiva de unidades/horas
        
        VALIDACIONES:
            - Se ejecutan en confirm(), permitiendo crear reservas "borrador"
            - Esto facilita pruebas y manejo de estados intermedios
        """
        self.customer = customer
        self.service = service
        self.quantity = quantity
        self.status = "Pending"      # Estado inicial: pendiente de confirmación
        self.total_cost = 0.0        # Se calcula al confirmar la reserva
        
        logging.debug(
            f"Reservation created: Customer={customer.entity_id}, "
            f"Service={service.name}, Quantity={quantity}, Status=Pending"
        )
    
    def confirm(self):
        """
        MÉTODO: Confirma la reserva calculando costo y validando reglas.
        
        PROCESO:
            1. Validar que el cliente esté activo
            2. Calcular costo total usando método del servicio
            3. Cambiar estado a "Confirmed"
            4. Registrar evento exitoso en logs
        
        MANEJO DE EXCEPCIONES - DEMOSTRACIÓN DE PATRONES:
            - try/except: Captura ValidationError y encadena en ProcessingError
            - try/except/else: Registra éxito solo si no hubo excepciones
            - try/except/finally: Limpieza y registro final siempre se ejecuta
        
        RAISES:
            ProcessingError: Si la validación o cálculo falla (con encadenamiento)
        """
        # Variable para controlar recursos (demostración de finally)
        recurso_temporal = None
        
        try:
            # VALIDACIÓN 1: Cliente debe estar activo
            if hasattr(self.customer, 'is_active') and not self.customer.is_active:
                raise ValidationError(
                    f"Cliente {self.customer.entity_id} está inactivo y no puede reservar",
                    "customer_status"
                )
            
            # VALIDACIÓN 2: Servicio debe ser instancia válida
            if not isinstance(self.service, Service):
                raise ValidationError("El servicio debe ser una instancia de la clase Service", "service")
            
            # CALCULAR COSTO: Método polimórfico del servicio
            # Esto demuestra POLIMORFISMO: cada servicio calcula diferente
            self.total_cost = self.service.calculate_cost(self.quantity)
            
            # CAMBIAR ESTADO: Solo si todo lo anterior fue exitoso
            self.status = "Confirmed"
            
        except ValidationError as e:
            # PATRÓN: try/except - Manejo específico de validación
            logging.warning(
                f"Validation failed for reservation confirmation | "
                f"Customer: {self.customer.entity_id} | Error: {e.mensaje}"
            )
            
            # PATRÓN: ENCADENAMIENTO DE EXCEPCIONES
            # 'from e' preserva el traceback original para debugging
            raise ProcessingError(
                "La reserva no pudo ser confirmada debido a reglas de validación",
                causa_original=e
            ) from e
            
        except Exception as e:
            # PATRÓN: try/except - Captura cualquier error inesperado
            logging.error(
                f"Unexpected error during reservation confirmation | "
                f"Customer: {self.customer.entity_id} | Exception: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise ProcessingError(f"Error inesperado al confirmar reserva: {e}", causa_original=e) from e
            
        else:
            # PATRÓN: try/except/else - Se ejecuta SOLO si NO hubo excepciones
            logging.info(
                f"Reservation confirmed successfully | "
                f"Customer: {self.customer.name} | Service: {self.service.name} | "
                f"Quantity: {self.quantity} | Total Cost: ${self.total_cost:.2f}"
            )
            
        finally:
            # PATRÓN: try/except/finally - SIEMPRE se ejecuta (limpieza de recursos)
            if recurso_temporal:
                # Ejemplo: cerrar archivo, liberar conexión, etc.
                pass
            # Registrar que el proceso de confirmación finalizó (éxito o fallo)
            logging.debug(f"Confirmation process completed for reservation | Status: {self.status}")
    
    def cancel(self, reason="No reason provided"):
        """
        MÉTODO: Cancela la reserva con motivo registrado.
        
        PARÁMETROS:
            reason (str, opcional): Motivo de la cancelación para auditoría
        
        VALIDACIONES:
            - No se puede cancelar una reserva ya cancelada
            - Se registra el motivo en logs para trazabilidad
        
        RAISES:
            ValidationError: Si la reserva ya está cancelada
        """
        try:
            # Validar que no esté ya cancelada
            if self.status == "Cancelled":
                raise ValidationError(
                    f"La reserva {id(self)} ya está cancelada",
                    "status"
                )
            
            # Cambiar estado a cancelado
            previous_status = self.status
            self.status = "Cancelled"
            
            # Registrar cancelación exitosa con motivo
            logging.info(
                f"Reservation cancelled | ID: {id(self)} | "
                f"Previous status: {previous_status} | Reason: {reason}"
            )
            
        except ValidationError as e:
            # Registrar intento de cancelar reserva ya cancelada
            logging.warning(
                f"Attempted to cancel already cancelled reservation | "
                f"Reservation ID: {id(self)} | Error: {e.mensaje}"
            )
            raise
        
        except Exception as e:
            # Capturar errores inesperados durante cancelación
            logging.error(
                f"Unexpected error during cancellation | Reservation ID: {id(self)} | "
                f"Exception: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise
    
    def __str__(self):
        """
        MÉTODO: Retorna representación textual de la reserva.
        
        RETURNS:
            str: Resumen con cliente, servicio, estado y costo
        """
        return (
            f"Reservation[ID:{id(self)}] | "
            f"Customer: {self.customer.name} | "
            f"Service: {self.service.name} | "
            f"Status: {self.status} | "
            f"Cost: ${self.total_cost:.2f}"
        )


# =============================================================================
# MÓDULO 5: GESTOR DEL SISTEMA (LISTAS INTERNAS + PERSISTENCIA EN MEMORIA)
# =============================================================================

class FJManager:
    """
    CLASE: Gestor central del sistema que administra listas en memoria.
    
    FUNCIONALIDAD:
    - Mantiene listas de clientes y reservas sin base de datos
    - Coordina la confirmación y registro de nuevas reservas
    - Garantiza unicidad de clientes mediante verificación
    
    PRINCIPIO POO: ENCAPSULAMIENTO + COMPOSICIÓN
    """
    
    def __init__(self):
        """
        CONSTRUCTOR: Inicializa listas vacías para gestión en memoria.
        
        ATRIBUTOS:
            customers (list): Lista de objetos Customer únicos
            reservations (list): Lista de objetos Reservation confirmados
        """
        self.customers = []       # Lista para almacenar clientes únicos
        self.reservations = []    # Lista para almacenar reservas confirmadas
        
        logging.info("FJManager initialized - Ready to manage customers and reservations")
    
    def add_reservation(self, res):
        """
        MÉTODO: Agrega una reserva al sistema después de confirmarla.
        
        PARÁMETROS:
            res (Reservation): Objeto reserva a agregar
        
        PROCESO:
            1. Confirmar la reserva (valida y calcula costo)
            2. Agregar a lista de reservas
            3. Agregar cliente a lista si es único (por ID)
        
        MANEJO DE EXCEPCIONES:
        - try/except/else: Manejo completo con registro diferenciado
        """
        try:
            # Confirmar reserva (puede lanzar ProcessingError)
            res.confirm()
            
        except ProcessingError as e:
            # Registrar fallo de confirmación
            logging.error(
                f"Failed to add reservation: {e.mensaje} | "
                f"Customer: {res.customer.entity_id} | Service: {res.service.name}"
            )
            raise  # Re-lanzar para que la UI maneje el error
            
        else:
            # PATRÓN: try/except/else - Solo si confirm() fue exitoso
            # Agregar reserva a lista principal
            self.reservations.append(res)
            
            # Agregar cliente si no existe ya (verificación por ID)
            if not any(c.entity_id == res.customer.entity_id for c in self.customers):
                self.customers.append(res.customer)
                logging.info(f"New customer added to system: {res.customer.name} (ID: {res.customer.entity_id})")
            
            logging.info(
                f"Reservation added successfully | Reservation ID: {id(res)} | "
                f"Total customers: {len(self.customers)} | Total reservations: {len(self.reservations)}"
            )
            
        finally:
            # PATRÓN: try/except/finally - Siempre registrar intento
            logging.debug(f"add_reservation() completed for customer {res.customer.entity_id}")


# =============================================================================
# MÓDULO 6: INTERFAZ GRÁFICA Y SIMULACIÓN (GUI + PRUEBAS)
# =============================================================================

class FJApp:
    """
    CLASE: Interfaz gráfica principal del sistema Software FJ.
    
    FUNCIONALIDAD:
    - Formulario para crear reservas manualmente
    - Botón para ejecutar simulación automática de 10 operaciones
    - Manejo de errores con mensajes amigables al usuario
    - Registro de todas las acciones en archivo de logs
    
    PRINCIPIO POO: ENCAPSULAMIENTO + MANEJO DE EXCEPCIONES EN UI
    """
    
    def __init__(self, root):
        """
        CONSTRUCTOR: Inicializa la ventana principal y componentes UI.
        
        PARÁMETROS:
            root (tk.Tk): Instancia principal de Tkinter
        """
        # Inicializar gestor del sistema (lógica de negocio)
        self.manager = FJManager()
        
        # Configurar ventana principal
        self.root = root
        self.root.title("FJ Advanced Management System")
        self.root.geometry("480x620")
        self.root.resizable(False, False)  # Ventana de tamaño fijo
        
        # Registrar inicio de interfaz en logs
        logging.info("FJApp GUI initialized")
        
        # Construir interfaz de usuario
        self._setup_ui()
    
    def _setup_ui(self):
        """
        MÉTODO PRIVADO: Configura todos los componentes de la interfaz.
        
        COMPONENTES:
        1. Título principal
        2. Campos de entrada: Nombre, ID, Servicio, Cantidad
        3. Botones: Procesar reserva, Ejecutar simulación
        4. Área de estado (opcional para expansión futura)
        """
        # --- TÍTULO PRINCIPAL ---
        tk.Label(
            self.root,
            text="FJ SYSTEM V2",
            font=("Arial", 18, "bold"),
            fg="#2c3e50"
        ).pack(pady=15)
        
        tk.Label(
            self.root,
            text="Software FJ - Reservation Management",
            font=("Arial", 10),
            fg="#7f8c8d"
        ).pack(pady=(0, 15))
        
        # --- CAMPOS DE ENTRADA ---
        # Campo: Nombre del cliente
        tk.Label(self.root, text="Customer Name:", anchor="w").pack(fill="x", padx=20)
        self.ent_name = tk.Entry(self.root, width=40)
        self.ent_name.pack(pady=(2, 10), padx=20)
        
        # Campo: ID del cliente
        tk.Label(self.root, text="Customer ID:", anchor="w").pack(fill="x", padx=20)
        self.ent_id = tk.Entry(self.root, width=40)
        self.ent_id.pack(pady=(2, 10), padx=20)
        
        # Campo: Tipo de servicio (Combobox)
        tk.Label(self.root, text="Service Type:", anchor="w").pack(fill="x", padx=20)
        self.combo = ttk.Combobox(
            self.root,
            values=["Room", "Equipment", "Consulting"],  # 3 servicios disponibles
            state="readonly",
            width=37
        )
        self.combo.pack(pady=(2, 10), padx=20)
        self.combo.current(0)  # Seleccionar primer valor por defecto
        
        # Campo: Cantidad de unidades
        tk.Label(self.root, text="Quantity (Units/Hours):", anchor="w").pack(fill="x", padx=20)
        self.ent_qty = tk.Entry(self.root, width=40)
        self.ent_qty.pack(pady=(2, 15), padx=20)
        
        # --- BOTONES DE ACCIÓN ---
        # Botón: Procesar reserva individual
        tk.Button(
            self.root,
            text="PROCESS RESERVATION",
            command=self.process_ui,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=10)
        
        # Botón: Ejecutar simulación de 10 operaciones
        tk.Button(
            self.root,
            text="RUN 10-OPS SIMULATION",
            command=self.run_simulation,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        # --- PIE DE PÁGINA ---
        tk.Label(
            self.root,
            text="UNAD - Programming Course 213023 | Phase 4",
            font=("Arial", 8),
            fg="#95a5a6"
        ).pack(side="bottom", pady=10)
    
    def process_ui(self):
        """
        MÉTODO: Procesa reserva desde interfaz gráfica con manejo robusto de errores.
        
        PROCESO:
            1. Obtener valores de campos de entrada
            2. Validar datos básicos (cantidad requerida, formato numérico)
            3. Crear objetos: Customer, Service, Reservation
            4. Confirmar y agregar reserva al sistema
            5. Mostrar resultado al usuario con messagebox
        
        MANEJO DE EXCEPCIONES - MÚLTIPLES PATRONES:
            - try/except: Captura excepciones específicas por tipo
            - Mensajes diferenciados: Validation vs Process vs Input vs Critical
            - Registro en logs de todos los intentos (éxito y fallo)
        """
        try:
            # OBTENER VALORES DE LA UI
            name = self.ent_name.get().strip()
            ident = self.ent_id.get().strip()
            serv_type = self.combo.get()
            qty_str = self.ent_qty.get().strip()
            
            # VALIDACIÓN BÁSICA: Cantidad es obligatoria
            if not qty_str:
                raise ValidationError("Quantity is required.", "quantity")
            
            # VALIDACIÓN BÁSICA: Cantidad debe ser número entero
            qty = int(qty_str)
            
            # CREAR OBJETO SERVICIO (Polimorfismo: 3 tipos disponibles)
            if serv_type == "Room":
                service = RoomReservation("Meeting Room", base_rate=50)
            elif serv_type == "Equipment":
                service = EquipmentRental("Tech Equipment", base_rate=30)
            elif serv_type == "Consulting":
                # Nuevo servicio: Consulting con nivel y modalidad
                service = ConsultingService(
                    "Technical Consultation",
                    base_rate=80,
                    consultant_level="senior",
                    modality="remota"
                )
            else:
                # Caso no debería ocurrir por Combobox readonly, pero por seguridad
                raise ServiceNotFoundError(serv_type)
            
            # CREAR OBJETO CLIENTE con validaciones robustas
            customer = Customer(name=name, customer_id=ident if ident else None)
            
            # CREAR Y CONFIRMAR RESERVA
            res = Reservation(customer=customer, service=service, quantity=qty)
            self.manager.add_reservation(res)  # Esto llama a res.confirm() internamente
            
            # ÉXITO: Mostrar confirmación al usuario
            messagebox.showinfo(
                "Success ✓",
                f"Reservation Confirmed!\n\n"
                f"Customer: {customer.name}\n"
                f"Service: {service.name}\n"
                f"Quantity: {qty}\n"
                f"Total with Taxes: ${res.total_cost:.2f}\n"
                f"Status: {res.status}"
            )
            
            # Registrar éxito en logs
            logging.info(f"UI Operation Successful: Customer '{name}' reserved {service.name}")
            
        except ValidationError as e:
            # PATRÓN: try/except - Manejo de errores de validación de datos
            messagebox.showwarning(
                "Validation Error ⚠️",
                f"Invalid input:\n\n{e.mensaje}\n\n"
                f"Field: {e.campo_afectado or 'N/A'}"
            )
            logging.warning(f"UI Validation Error: {e.mensaje} | Field: {e.campo_afectado}")
            
        except ProcessingError as e:
            # PATRÓN: try/except - Manejo de errores de procesamiento de negocio
            messagebox.showwarning(
                "Process Error ⚠️",
                f"Could not process reservation:\n\n{e.mensaje}"
            )
            logging.warning(f"UI Processing Error: {e.mensaje}")
            # Mostrar causa original si existe (encadenamiento)
            if e.causa_original:
                logging.debug(f"Root cause: {type(e.causa_original).__name__}: {e.causa_original}")
                
        except ValueError:
            # PATRÓN: try/except - Manejo de error de conversión de tipos
            messagebox.showerror(
                "Input Error ✗",
                "Quantity must be a valid whole number.\n\nExample: 5, 10, 24"
            )
            logging.error("UI Input Error: Quantity is not a valid integer")
            
        except ServiceNotFoundError as e:
            # PATRÓN: try/except - Manejo de servicio no encontrado
            messagebox.showerror(
                "Service Error ✗",
                f"Service not available:\n\n{e.mensaje}"
            )
            logging.error(f"UI Service Error: {e.mensaje}")
            
        except Exception as e:
            # PATRÓN: try/except - Captura CUALQUIER error inesperado
            messagebox.showerror(
                "Critical Error ✗",
                f"Unexpected error occurred:\n\n{type(e).__name__}: {e}\n\n"
                f"Please try again or contact support."
            )
            logging.critical(
                f"UI Critical Error: {type(e).__name__}: {e}",
                exc_info=True  # Incluir traceback completo
            )
    
    def run_simulation(self):
        """
        MÉTODO: Ejecuta simulación automática de 10 operaciones para demostrar robustez.
        
        PROPÓSITO:
        - Demostrar que el sistema maneja tanto casos válidos como inválidos
        - Verificar que la aplicación NO se cierra ante errores
        - Generar registros en logs para auditoría
        
        CASOS DE PRUEBA (10 operaciones):
        1-2-3: Clientes válidos con diferentes servicios → ÉXITO
        4: Cliente sin nombre → ERROR DE VALIDACIÓN
        5: Cliente válido → ÉXITO
        6: Cantidad negativa → ERROR DE VALIDACIÓN
        7-8-9: Clientes válidos → ÉXITO
        10: Cantidad cero → ERROR DE VALIDACIÓN
        
        MANEJO DE EXCEPCIONES:
        - Cada operación en su propio try/except
        - Registro detallado en consola y logs
        - La simulación continúa incluso si una operación falla
        """
        # Registrar inicio de simulación en logs
        logging.info("=== STARTING 10-OPERATION SIMULATION ===")
        print("\n" + "="*70)
        print("  SIMULACIÓN AUTOMÁTICA - 10 OPERACIONES")
        print("  Casos válidos e inválidos para demostrar manejo de excepciones")
        print("="*70 + "\n")
        
        # DATOS DE PRUEBA: Lista de tuplas (nombre, ID, servicio, cantidad)
        # Incluye casos válidos (✓) e inválidos (✗) para probar robustez
        test_data = [
            # CASOS VÁLIDOS (deben procesarse exitosamente)
            ("Alice Johnson", "C001", "Room", 5),           # ✓ Cliente válido + sala
            ("Bob Smith", "C002", "Equipment", 10),         # ✓ Cliente válido + equipo
            ("Charlie Brown", "C003", "Consulting", 3),     # ✓ Cliente válido + asesoría
            ("Diana Prince", "C004", "Room", 8),            # ✓ Otro cliente válido
            ("Eve Wilson", "C005", "Equipment", 2),         # ✓ Cliente + equipo corto
            
            # CASOS INVÁLIDOS (deben fallar con manejo controlado)
            ("", "C006", "Room", 5),                        # ✗ Nombre vacío → ValidationError
            ("Frank Miller", "C007", "Consulting", -1),     # ✗ Cantidad negativa → ValidationError
            ("Grace Lee", "C008", "Room", 0),               # ✗ Cantidad cero → ValidationError
            ("123Invalid", "C009", "Equipment", 4),         # ✗ Nombre con números → ValidationError
            ("Heidi Clark", "C010", "Consulting", 12),      # ✓ Último caso válido
        ]
        
        # CONTADORES PARA RESUMEN FINAL
        success_count = 0
        error_count = 0
        
        # PROCESAR CADA CASO DE PRUEBA
        for i, (name, cust_id, service_type, quantity) in enumerate(test_data, start=1):
            print(f"\n📋 Operación #{i}: '{name}' | Servicio: {service_type} | Cantidad: {quantity}")
            print("-"*70)
            
            try:
                # VALIDACIÓN PRELIMINAR: Cantidad debe ser número
                if not isinstance(quantity, int) or quantity <= 0:
                    raise ValidationError(
                        f"Quantity must be positive integer: {quantity}",
                        "quantity"
                    )
                
                # CREAR SERVICIO (Polimorfismo: 3 tipos)
                if service_type == "Room":
                    service = RoomReservation("Meeting Room", base_rate=50)
                elif service_type == "Equipment":
                    service = EquipmentRental("Tech Equipment", base_rate=30)
                elif service_type == "Consulting":
                    service = ConsultingService(
                        "Technical Consultation",
                        base_rate=80,
                        consultant_level="senior",
                        modality="remota"
                    )
                else:
                    raise ServiceNotFoundError(service_type)
                
                # CREAR CLIENTE (con validaciones robustas)
                customer = Customer(name=name, customer_id=cust_id)
                
                # CREAR Y CONFIRMAR RESERVA
                reservation = Reservation(customer=customer, service=service, quantity=quantity)
                self.manager.add_reservation(reservation)
                
                # ÉXITO: Mostrar detalles en consola
                print(f"   ✅ SUCCESS | Total: ${reservation.total_cost:.2f} | Status: {reservation.status}")
                print(f"      Customer: {customer.name} (ID: {customer.entity_id})")
                print(f"      Service: {service.get_description()}")
                
                # Registrar éxito en logs
                logging.info(
                    f"Simulation Op #{i} SUCCESS | Customer: {name} | "
                    f"Service: {service_type} | Cost: ${reservation.total_cost:.2f}"
                )
                
                success_count += 1
                
            except ValidationError as e:
                # MANEJO: Error de validación de datos de entrada
                print(f"   ⚠️ EXPECTED VALIDATION ERROR: {e.mensaje}")
                if e.campo_afectado:
                    print(f"      Affected field: '{e.campo_afectado}'")
                
                # Verificar encadenamiento de excepciones si existe
                # Esto demuestra el patrón: raise ProcessingError(...) from ValidationError
                if hasattr(e, '__cause__') and e.__cause__:
                    print(f"      Root cause (chained): {type(e.__cause__).__name__}")
                
                # Registrar error esperado en logs (no es crítico)
                logging.warning(
                    f"Simulation Op #{i} VALIDATION ERROR | Customer: {name} | "
                    f"Field: {e.campo_afectado} | Message: {e.mensaje}"
                )
                
                error_count += 1
                
            except ProcessingError as e:
                # MANEJO: Error de procesamiento de negocio
                print(f"   ⚠️ EXPECTED PROCESSING ERROR: {e.mensaje}")
                
                # Mostrar causa original si hay encadenamiento
                if e.causa_original:
                    print(f"      Root cause: {type(e.causa_original).__name__}: {e.causa_original}")
                
                logging.warning(
                    f"Simulation Op #{i} PROCESSING ERROR | Customer: {name} | "
                    f"Message: {e.mensaje}"
                )
                
                error_count += 1
                
            except ServiceNotFoundError as e:
                # MANEJO: Servicio no encontrado (caso de seguridad)
                print(f"   ✗ SERVICE NOT FOUND: {e.mensaje}")
                logging.error(f"Simulation Op #{i} SERVICE ERROR | {e.mensaje}")
                error_count += 1
                
            except ValueError as e:
                # MANEJO: Error de conversión de tipos
                print(f"   ✗ INPUT FORMAT ERROR: Quantity must be a number")
                logging.error(f"Simulation Op #{i} VALUE ERROR | {e}")
                error_count += 1
                
            except Exception as e:
                # MANEJO: CUALQUIER otro error inesperado
                print(f"   ✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
                logging.critical(
                    f"Simulation Op #{i} UNEXPECTED ERROR | {type(e).__name__}: {e}",
                    exc_info=True
                )
                error_count += 1
        
        # MOSTRAR RESUMEN FINAL DE SIMULACIÓN
        print("\n" + "="*70)
        print("  SIMULACIÓN COMPLETADA")
        print("="*70)
        print(f"  ✅ Operaciones exitosas: {success_count}")
        print(f"  ⚠️ Operaciones con error (manejadas): {error_count}")
        print(f"  📊 Total de operaciones: {len(test_data)}")
        print(f"\n  📁 Revisar archivo 'fj_management_v2.log' para detalles completos")
        print(f"  🔍 La aplicación se mantuvo ESTABLE durante toda la ejecución")
        print("="*70 + "\n")
        
        # Registrar finalización de simulación en logs
        logging.info(
            f"=== SIMULATION COMPLETED | Success: {success_count} | Errors: {error_count} ==="
        )
        
        # Mostrar mensaje al usuario vía GUI
        messagebox.showinfo(
            "Simulation Complete ✓",
            f"10 operations processed:\n\n"
            f"✅ Successful: {success_count}\n"
            f"⚠️ Errors handled: {error_count}\n\n"
            f"Check the terminal/console for detailed results.\n"
            f"All events logged in 'fj_management_v2.log'"
        )


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL DEL PROGRAMA
# =============================================================================

if __name__ == "__main__":
    """
    BLOQUE PRINCIPAL DE EJECUCIÓN:
    
    PROPÓSITO:
    - Iniciar la interfaz gráfica del sistema Software FJ
    - Mantener la aplicación activa hasta que el usuario la cierre
    - Manejar interrupciones externas (Ctrl+C) de forma controlada
    
    PRINCIPIO: PUNTO DE ENTRADA ESTÁNDAR DE PYTHON
    - if __name__ == "__main__": asegura que este código solo se ejecute
      cuando el archivo se corre directamente, no cuando se importa como módulo
    """
    
    try:
        # Crear ventana principal de Tkinter
        root = tk.Tk()
        
        # Inicializar aplicación con la ventana
        app = FJApp(root)
        
        # Iniciar bucle principal de eventos de la GUI
        # Este método bloquea la ejecución hasta que se cierra la ventana
        logging.info("Starting Tkinter mainloop - Application ready")
        root.mainloop()
        
    except KeyboardInterrupt:
        # MANEJO: Interrupción por usuario (Ctrl+C en consola)
        print("\n\n⚠️ Sistema interrumpido por el usuario (KeyboardInterrupt)")
        logging.warning("Application interrupted by user via KeyboardInterrupt")
        
    except tk.TclError as e:
        # MANEJO: Errores específicos de Tkinter (ej: ventana cerrada inesperadamente)
        print(f"\n✗ GUI Error: {e}")
        logging.error(f"Tkinter error: {e}")
        
    except Exception as e:
        # MANEJO: CUALQUIER error crítico no manejado
        print(f"\n✗ CRITICAL ERROR: {type(e).__name__}: {e}")
        logging.critical(
            f"Unhandled critical error: {type(e).__name__}: {e}",
            exc_info=True
        )
        
    finally:
        # PATRÓN: try/except/finally - SIEMPRE se ejecuta al finalizar
        # Registrar cierre del sistema para auditoría
        logging.info("=== APPLICATION CLOSED ===")
        print("\n✓ Sistema cerrado correctamente - Revisar logs para auditoría")