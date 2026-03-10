# LICIT — Herramienta para gestión de licitaciones

LICIT es una herramienta en desarrollo para **gestionar el proceso completo de preparación y seguimiento de licitaciones**, desde el registro inicial hasta la adjudicación y generación de documentación.

El objetivo es disponer de una aplicación que permita:

- registrar licitaciones aunque finalmente no se presenten
- gestionar lotes y decidir a cuáles presentarse
- controlar el proceso de preparación
- gestionar empresas participantes (individuales o en UTE)
- preparar automáticamente anexos de oferta y adjudicación
- registrar resultados y adjudicatarios

El proyecto está diseñado con **Python, arquitectura hexagonal y principios de DDD (Domain Driven Design)**.

---

# Estado actual del proyecto

Actualmente está implementado el **núcleo del dominio de licitaciones**, incluyendo:

- agregados de dominio
- entidades internas
- eventos de dominio
- reglas de negocio de participación en UTE
- lógica de selección de empresas firmantes según el tipo de anexo
- suite de tests del dominio

---

# Arquitectura

El proyecto sigue una arquitectura inspirada en **Hexagonal Architecture (Ports & Adapters)**.

# Estructura del proyecto
licit/
│
├─ domain/
│ ├─ licitacion/
│ │ ├─ models.py
│ │ └─ events.py
│ │
│ ├─ anexos/
│ │ └─ models.py
│ │
│ └─ terceros/
│ └─ models.py
│
├─ application/ # casos de uso (pendiente)
├─ infrastructure/ # persistencia (pendiente)
├─ cli/ # interfaz CLI (pendiente)
│
└─ tests/


---

# Dominio implementado

## Agregado principal

### `Licitacion`

Representa una licitación completa.

Responsabilidades principales:

- gestionar lotes
- gestionar empresas participantes
- controlar reglas de participación (individual / UTE)
- generar eventos de dominio
- calcular importes derivados
- determinar empresas firmantes según el tipo de anexo

---

## Entidades

### `Lote`

Representa un lote de la licitación.

Campos relevantes:

- `num_lote`
- `importe_lote`
- `nombre_lote`
- `descripcion`
- `a_presentar`

La licitación calcula automáticamente:

- `importe_licit`
- `importe_a_presentar`

---

### `EmpresaEnLicitacion`

Entidad interna del agregado `Licitacion`.

Representa la participación de una empresa concreta en la licitación.

Campos:

- `empresa_id`
- `representacion_id`
- `rol`

Roles posibles:
- INDIVIDUAL
- UTE_MIEMBRO
- UTE_CONSTITUIDA


---

# Reglas de negocio implementadas

## Participación de empresas

Una licitación puede tener:

- una empresa individual **o**
- varias empresas miembro de UTE

pero **nunca ambas a la vez**.

---

## UTE constituida

La UTE constituida:
- solo puede añadirse si existen miembros de UTE
- solo puede existir **una**
- una vez constituida, no se pueden añadir más miembros
- no se pueden eliminar miembros mientras exista la UTE

---

## Anulación de licitación

Una licitación anulada:
- no permite modificaciones
- sí permite consultas

---

# Selección de empresas firmantes
El agregado `Licitacion` puede determinar qué empresas deben firmar un anexo según su tipo.

Tipos de firma soportados:
- INDIVIDUAL_EMPRESA
- CONJUNTO_EMPRESAS
- UTE_CONSTITUIDA

Ejemplo:

| Tipo de anexo      | Empresas firmantes        |
|--------------------|---------------------------|
| INDIVIDUAL_EMPRESA | cada empresa participante |
| CONJUNTO_EMPRESAS  | empresas miembro de UTE   |
| UTE_CONSTITUIDA    | la UTE constituida        |

---

# Eventos de dominio

Actualmente se generan eventos para cambios en la presentación de lotes.

Eventos implementados:
- LoteMarcadoParaPresentar
- LoteDesmarcadoParaPresentar

Los eventos se almacenan en el agregado y pueden recuperarse mediante:
**pull_events()**


---

# Tests
El dominio está cubierto por una suite de tests basada en **pytest**.

Se testean:
- creación de licitación
- cálculo de importes
- validación de duplicados
- reglas de UTE
- anulación y reactivación
- eventos de dominio
- selección de empresas firmantes

Los tests utilizan **fixtures de fábrica** para simplificar la creación de escenarios.

---

# Próximos pasos

Los siguientes módulos previstos son:

### Application layer

Casos de uso como:
- crear licitación
- registrar empresas
- preparar anexos
- registrar adjudicación

---

### Generación de anexos

Sistema para:
- determinar qué anexos deben generarse
- rellenar automáticamente datos de empresas y apoderados
- generar anexos individuales o conjuntos
- gestionar anexos de oferta y adjudicación

---

### Persistencia

Persistencia mediante **SQLite**.

---

### CLI

Interfaz de línea de comandos basada en **Typer** para gestionar:
- licitaciones
- lotes
- empresas
- anexos

---

# Filosofía del proyecto

El objetivo del proyecto no es solo funcional, sino también **formativo**, priorizando:

- claridad de modelo de dominio
- separación de responsabilidades
- testabilidad
- comprensión de alternativas de diseño

---

# Estado

Proyecto en desarrollo activo.