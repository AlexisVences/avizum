# Revisión de seguridad general (Fase 5, paso 3) — 2026-10-20

Herramientas: `pip-audit` (dependencias de producción del backend), `bandit` (código del backend), `npm audit --omit=dev`
(frontend) y lectura de la configuración de autenticación, CORS y cabeceras. Semgrep (plugin) solo lee escaneos ya subidos a su
plataforma; este repositorio no tiene ninguno, así que no se usó.

## Hallazgos y qué se hizo

| Área | Hallazgo | Resolución |
|---|---|---|
| Backend, dependencias | 32 vulnerabilidades conocidas: Starlette 0.46.2 (FastAPI estaba fijado a <0.116), PyJWT 2.13, urllib3 2.7, certifi | Actualizados (FastAPI 0.156, Starlette 1.9, PyJWT 2.15, urllib3 2.8, certifi 2026.10.19). `pip-audit`: sin vulnerabilidades. 257 pruebas pasan, incluido el streaming |
| Backend, código | `bandit`: 0 hallazgos medios o altos (2 bajos) | — |
| Frontend, dependencias | `axios` con 3 avisos (uno alto: ReDoS en `fromDataURI`) | Actualizado a 1.20. Quedan 86 avisos en la cadena de `react-scripts` (CRA), que es herramienta de compilación y no se publica en el sitio |
| Cabeceras | La API no enviaba cabeceras de seguridad | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `CORP`, `Cache-Control: no-store` (middleware ASGI puro para no romper la detección de cierre del stream) |
| Documentación de la API | `/docs` y `/openapi.json` expuestos | Desactivados con `ENVIRONMENT=production` |
| JWT | Algoritmo fijado, `exp` verificado, secreto de desarrollo bloqueado en producción (paso 2) | — |
| CORS | Orígenes explícitos, métodos y cabeceras acotados | Sin cambios |

## Riesgos aceptados o pendientes

- El token JWT vive en `localStorage`: un XSS lo robaría. Mitigado por el renderizado sin HTML crudo y sin enlaces del modelo, y por la
  expiración de 60 min; pasar a cookie `HttpOnly` requiere CSRF y cambiar el flujo de autenticación (no se hizo).
- Registro responde 409 si el correo existe (permite enumerar cuentas); se acepta a cambio de una mejor experiencia y se limita por IP.
- Sin recuperación de contraseña ni verificación de correo (fuera de alcance actual).
- Los avisos de `react-scripts` se resuelven al migrar de CRA a Vite, trabajo aparte.
