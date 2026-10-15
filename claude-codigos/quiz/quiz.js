// Trivia de ingeniería de prompts — datos y vistas puras (HTML strings).
// Lo usan quiz.html (interactivo) y anim.html (render del vídeo).
const QZ_QUESTIONS = [
  { q: '¿Qué es la «cadena de pensamiento» al escribir prompts?',
    o: ['Conectar varios modelos distintos en secuencia', 'Una técnica de ajuste fino del modelo',
        'Pedir al modelo que razone paso a paso antes de responder', 'Un tipo de representación vectorial del texto'],
    a: 2, e: 'Cuando el modelo razona en voz alta, rinde mucho mejor en problemas de lógica y matemáticas.' },
  { q: '¿Cuál de estas NO es una buena práctica al escribir prompts?',
    o: ['Definir un rol para el modelo', 'Ser vago y dejar que el modelo decida todo',
        'Dar contexto y ejemplos relevantes', 'Especificar el formato exacto de la respuesta'],
    a: 1, e: 'La vaguedad es enemiga de los buenos prompts. Cuanto más claro sea el contexto, el formato y el objetivo, mejor será el resultado.' },
  { q: '¿Para qué sirve principalmente el prompt de sistema?',
    o: ['Para borrar la memoria del modelo', 'Para definir el comportamiento, el rol y las reglas desde el inicio',
        'Para configurar la clave de la API', 'Para cambiar el idioma del teclado'],
    a: 1, e: 'El prompt de sistema marca el marco de toda la conversación: quién es el modelo, cómo debe actuar y qué reglas sigue.' },
  { q: '¿Qué aporta incluir ejemplos dentro del prompt?',
    o: ['Hace que la respuesta sea más corta', 'Obliga a usar un modelo más pequeño',
        'No aporta nada', 'Muestra al modelo el patrón y el estilo que esperas'],
    a: 3, e: 'Con unos pocos ejemplos bien elegidos, el modelo entiende el patrón que buscas sin necesidad de reentrenarlo.' },
  { q: 'Si el modelo se inventa datos, una estrategia eficaz es:',
    o: ['Subir la temperatura al máximo', 'Borrar todo el contexto anterior',
        'Escribir el prompt entero en mayúsculas', 'Permitirle decir «no lo sé» y pedirle fuentes'],
    a: 3, e: 'Dar permiso explícito para decir «no lo sé» reduce mucho las invenciones. Pedir fuentes también facilita comprobarlas.' },
  { q: '¿Qué ocurre al subir la temperatura del modelo?',
    o: ['Las respuestas son más variadas y creativas', 'El modelo responde más rápido',
        'Las respuestas son siempre idénticas', 'Aumenta el límite de texto'],
    a: 0, e: 'La temperatura controla el azar. Alta: más creatividad y variedad. Baja: respuestas más predecibles y constantes.' },
  { q: '¿Cuál es la mejor forma de obtener una respuesta en JSON válido?',
    o: ['Pedir «responde en un formato bonito»', 'Indicar el esquema exacto con un ejemplo',
        'Esperar a que el modelo lo adivine', 'Escribir el prompt en otro idioma'],
    a: 1, e: 'Mostrar el esquema exacto (campos, tipos y un ejemplo) elimina la ambigüedad y hace la respuesta fácil de procesar.' },
  { q: '¿Qué significa encadenar prompts?',
    o: ['Copiar el mismo prompt varias veces', 'Usar emojis para unir ideas',
        'Dividir una tarea compleja en pasos que se alimentan entre sí', 'Bloquear el modelo con una contraseña'],
    a: 2, e: 'Cada paso hace una sola cosa bien y su resultado alimenta al siguiente. Así se resuelven tareas largas con más precisión.' },
  { q: 'Pedir «Actúa como un abogado laboralista» sirve para…',
    o: ['Darle acceso a bases de datos legales', 'Orientar el tono, el vocabulario y la profundidad',
        'Que la respuesta tenga validez legal', 'Nada: el modelo ignora los roles'],
    a: 1, e: 'Asignar un rol enfoca el registro y el nivel de detalle. No le da conocimientos nuevos, pero sí orienta los que ya tiene.' },
  { q: '¿Para qué sirven los delimitadores, como las comillas triples?',
    o: ['Para separar las instrucciones del texto que se debe procesar', 'Para que el texto se vea más elegante',
        'Para reducir el coste de uso', 'Para activar el modo creativo'],
    a: 0, e: 'Los delimitadores dejan claro qué es instrucción y qué es material de trabajo, y evitan que el modelo los mezcle.' },
];

const QZ_LEVELS = [
  { min: 0, name: 'Principiante', d: 'Estás empezando. Repasa lo básico: contexto y formato.' },
  { min: 3, name: 'Aprendiz', d: 'Conoces las bases, pero todavía dejas mucho al azar.' },
  { min: 5, name: 'Intermedio', d: 'Buen nivel. Te falta convertirlo en un sistema.' },
  { min: 7, name: 'Avanzado', d: 'Dominas las técnicas clave y ya sacas resultados reales.' },
  { min: 9, name: 'Maestro', d: 'Piensas como el modelo. Prompts de otro nivel.' },
];
const qzLevel = s => [...QZ_LEVELS].reverse().find(l => s >= l.min);
const LETTERS = ['A', 'B', 'C', 'D'];
const QZ_STAR = '<svg width="13" height="13" viewBox="0 0 24 24"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5-4.8-4.6 6.6-.9z" fill="currentColor"/></svg>';
const QZ_OK = '<svg width="14" height="14" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const QZ_NO = '<svg width="14" height="14" viewBox="0 0 24 24"><path d="M7 7l10 10M17 7 7 17" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>';

function qzStartView() {
  return `<div class="qz-screen qz-start">
    <div class="qz-badge"><svg width="44" height="44" viewBox="0 0 24 24"><path d="M9.2 9.2a2.9 2.9 0 1 1 4.1 2.6c-.8.4-1.3 1.1-1.3 2v.7" fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round"/><circle cx="12" cy="18" r="1.4" fill="#fff"/></svg></div>
    <div class="qz-eyebrow">Trivia interactiva</div>
    <h1 class="qz-title">¿Cuánto sabes de ingeniería de prompts?</h1>
    <p class="qz-desc">Responde 10 preguntas y descubre tu nivel. Al final verás tu puntuación y tu puesto en la clasificación.</p>
    <div class="qz-chips"><span><b>10</b> preguntas</span><span><b>4</b> opciones</span><span><b>5</b> niveles</span></div>
    <button class="qz-btn" data-act="start">Empezar el desafío</button>
    <div class="qz-note">Sin registro · Sin límite de tiempo</div>
  </div>`;
}

// sel: índice elegido o null; score: puntos acumulados (ya incluye esta respuesta si sel != null)
function qzQuestionView(i, sel, score) {
  const Q = QZ_QUESTIONS[i], answered = sel != null, ok = sel === Q.a, N = QZ_QUESTIONS.length;
  const segs = QZ_QUESTIONS.map((_, k) => `<i class="${k < i || (k === i && answered) ? 'done' : k === i ? 'cur' : ''}"></i>`).join('');
  const opts = Q.o.map((o, k) => {
    let cls = '', mark = `<span class="qz-l">${LETTERS[k]}</span>`;
    if (answered) {
      if (k === Q.a) { cls = 'ok'; mark = `<span class="qz-l">${QZ_OK}</span>`; }
      else if (k === sel) { cls = 'bad'; mark = `<span class="qz-l">${QZ_NO}</span>`; }
      else cls = 'dim';
    }
    return `<button class="qz-opt ${cls}" data-opt="${k}">${mark}<span class="qz-t">${o}</span></button>`;
  }).join('');
  return `<div class="qz-screen qz-q">
    <div class="qz-top"><span class="qz-count">Pregunta ${i + 1} de ${N}</span><span class="qz-pts">${QZ_STAR} ${score} ${score === 1 ? 'punto' : 'puntos'}</span></div>
    <div class="qz-segs">${segs}</div>
    <div class="qz-card"><h2 class="qz-question">${Q.q}</h2></div>
    <div class="qz-opts">${opts}</div>
    <div class="qz-fb ${answered ? (ok ? 'show ok' : 'show bad') : ''}">
      <div class="qz-fbt">${ok ? '¡Correcto! +1 punto' : 'Esta vez no'}</div><p>${Q.e}</p>
    </div>
    <button class="qz-btn ${answered ? '' : 'hidden'}" data-act="next">${i + 1 < N ? 'Siguiente pregunta' : 'Ver mi resultado'}</button>
  </div>`;
}

function qzResultView(score) {
  const lv = qzLevel(score), N = QZ_QUESTIONS.length, C = 2 * Math.PI * 52;
  const rows = [...QZ_LEVELS].reverse().map((l, k) =>
    `<li class="${l === lv ? 'me' : ''}"><span class="qz-pos">${k + 1}</span><span class="qz-ln">${l.name}</span><span class="qz-lp">${l.min}+ pts</span></li>`).join('');
  return `<div class="qz-screen qz-res">
    <div class="qz-eyebrow">Tu resultado</div>
    <div class="qz-ring"><svg width="132" height="132" viewBox="0 0 120 120"><circle cx="60" cy="60" r="52" fill="none" stroke="#E7E3F3" stroke-width="10"/>
      <circle cx="60" cy="60" r="52" fill="none" stroke="#5B4BF5" stroke-width="10" stroke-linecap="round" stroke-dasharray="${C * score / N} ${C}" transform="rotate(-90 60 60)"/></svg>
      <div><b>${score}</b><span>de ${N}</span></div></div>
    <div class="qz-level">${lv.name}</div>
    <p class="qz-desc">${lv.d}</p>
    <div class="qz-eyebrow">Clasificación</div>
    <ol class="qz-rank">${rows}</ol>
    <button class="qz-btn" data-act="restart">Jugar de nuevo</button>
  </div>`;
}
