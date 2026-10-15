// Quiz de prompt engineering — datos y vistas puras (HTML strings).
// Lo usan quiz.html (interactivo) y anim.html (render del vídeo).
const QZ_QUESTIONS = [
  { q: '¿Qué es Chain of Thought (cadena de pensamiento)?',
    o: ['Conectar varios modelos distintos en secuencia', 'Una técnica de fine-tuning de modelos',
        'Pedir al modelo que muestre su razonamiento paso a paso antes de responder', 'Un tipo de embedding semántico'],
    a: 2, e: 'Chain of Thought hace que el modelo piense en voz alta. Mejora mucho el rendimiento en tareas de razonamiento matemático y lógico.' },
  { q: '¿Cuál de estas NO es una buena práctica de prompt engineering?',
    o: ['Definir un rol o persona para el modelo', 'Ser vago y dejar que el modelo decida todo',
        'Dar contexto y ejemplos relevantes', 'Especificar el formato exacto de salida'],
    a: 1, e: 'La vaguedad es enemiga de los buenos prompts. Cuanto más específico seas con el contexto, el formato y el objetivo, mejor será el resultado.' },
  { q: '¿Para qué sirve principalmente el system prompt?',
    o: ['Para borrar la memoria del modelo', 'Para definir comportamiento, rol y reglas antes de la conversación',
        'Para configurar la API key', 'Para cambiar el idioma del teclado'],
    a: 1, e: 'El system prompt marca el marco de toda la conversación: quién es el modelo, cómo debe actuar y qué reglas debe seguir.' },
  { q: '¿Qué es few-shot prompting?',
    o: ['Hacer pocas preguntas por sesión', 'Limitar la respuesta a pocas palabras',
        'Usar un modelo más pequeño', 'Incluir ejemplos del resultado esperado dentro del prompt'],
    a: 3, e: 'Con unos pocos ejemplos bien elegidos, el modelo entiende el patrón y el estilo que buscas sin necesidad de reentrenarlo.' },
  { q: 'Cuando el modelo alucina (inventa datos), una estrategia eficaz es:',
    o: ['Subir la temperatura al máximo', 'Borrar todo el contexto anterior',
        'Escribir el prompt entero en mayúsculas', 'Permitirle decir «no lo sé» y pedirle que cite fuentes'],
    a: 3, e: 'Dar permiso explícito para decir «no lo sé» reduce drásticamente las alucinaciones. Pedir fuentes también mejora la verificabilidad.' },
  { q: '¿Qué ocurre al subir la temperatura del modelo?',
    o: ['Las respuestas son más variadas y creativas', 'El modelo responde más rápido',
        'Las respuestas son siempre idénticas', 'Aumenta el límite de tokens'],
    a: 0, e: 'La temperatura controla la aleatoriedad. Alta: más creatividad y variedad. Baja: respuestas más predecibles y consistentes.' },
  { q: '¿Cuál es la mejor forma de obtener una respuesta en JSON válido?',
    o: ['Pedir «responde en un formato bonito»', 'Especificar el esquema exacto con un ejemplo',
        'Esperar a que el modelo lo adivine', 'Escribir el prompt en inglés'],
    a: 1, e: 'Mostrar el esquema exacto (claves, tipos y un ejemplo) elimina la ambigüedad y hace que la salida sea fácil de procesar.' },
  { q: '¿Qué es prompt chaining?',
    o: ['Copiar el mismo prompt varias veces', 'Usar emojis para encadenar ideas',
        'Dividir una tarea compleja en pasos encadenados', 'Bloquear el modelo con una contraseña'],
    a: 2, e: 'Encadenar prompts permite que cada paso haga una sola cosa bien, y la salida de uno alimenta al siguiente.' },
  { q: 'Pedir al modelo «Actúa como un abogado laboralista» sirve para…',
    o: ['Darle acceso a bases de datos legales', 'Orientar el tono, el vocabulario y la profundidad',
        'Que la respuesta tenga validez legal', 'Nada: el modelo ignora los roles'],
    a: 1, e: 'Asignar un rol orienta el registro y el nivel de detalle. No le da conocimientos nuevos, pero sí enfoca los que ya tiene.' },
  { q: '¿Para qué sirven los delimitadores (comillas triples o etiquetas XML)?',
    o: ['Para separar las instrucciones del contenido que se debe procesar', 'Para que el texto se vea más elegante',
        'Para reducir el coste de la API', 'Para activar el modo creativo'],
    a: 0, e: 'Los delimitadores dejan claro qué es instrucción y qué es material de trabajo, y evitan que el modelo los confunda.' },
];

const QZ_LEVELS = [
  { min: 0, name: 'Principiante', d: 'Estás empezando. Repasa lo básico de contexto y formato.' },
  { min: 3, name: 'Aprendiz', d: 'Conoces las bases, pero aún dejas mucho al azar.' },
  { min: 5, name: 'Intermedio', d: 'Buen nivel. Te falta convertirlo en sistema.' },
  { min: 7, name: 'Avanzado', d: 'Dominas las técnicas clave. Ya sacas resultados reales.' },
  { min: 9, name: 'Maestro', d: 'Piensas como el modelo. Prompts de otro nivel.' },
];
const qzLevel = s => [...QZ_LEVELS].reverse().find(l => s >= l.min);
const pad2 = n => String(n).padStart(2, '0');
const LETTERS = ['A', 'B', 'C', 'D'];

function qzStartView() {
  return `<div class="qz-screen qz-start">
    <div class="qz-meta"><span><i class="qz-dot"></i>QUIZ INTERACTIVO</span><span>V.01</span></div>
    <div class="qz-kicker">— DESAFÍO</div>
    <h1 class="qz-title">¿Eres de verdad<br>un <em>maestro</em><br>de los prompts<em>?</em></h1>
    <div class="qz-rule"></div>
    <p class="qz-desc">Diez preguntas. Cuatro alternativas cada una. Un ranking final que te dirá si dominas el prompt engineering o si todavía te queda camino.</p>
    <div class="qz-stats">
      <div><b>10</b><span>PREGUNTAS</span></div><div><b>~3</b><span>MINUTOS</span></div><div><b>05</b><span>NIVELES</span></div>
    </div>
    <button class="qz-btn" data-act="start">INICIAR DESAFÍO →</button>
    <div class="qz-foot">// sin registro. sin cronómetro. solo tú y el modelo.</div>
  </div>`;
}

// sel: índice elegido o null; score: puntos acumulados (ya incluye esta respuesta si sel != null)
function qzQuestionView(i, sel, score) {
  const Q = QZ_QUESTIONS[i], answered = sel != null, ok = sel === Q.a;
  const opts = Q.o.map((o, k) => {
    let cls = '', mark = '';
    if (answered) {
      if (k === Q.a) { cls = 'ok'; mark = '✓'; }
      else if (k === sel) { cls = 'bad'; mark = '×'; }
      else cls = 'dim';
    }
    return `<button class="qz-opt ${cls}" data-opt="${k}"><span class="qz-l">${LETTERS[k]}</span><span class="qz-t">${o}</span><span class="qz-m">${mark}</span></button>`;
  }).join('');
  return `<div class="qz-screen qz-q">
    <div class="qz-meta"><span>PREGUNTA ${pad2(i + 1)} / ${QZ_QUESTIONS.length}</span><span class="qz-pts"><i class="qz-dot"></i>PUNTOS: ${score}</span></div>
    <div class="qz-prog"><i style="width:${(i + (answered ? 1 : 0)) / QZ_QUESTIONS.length * 100}%"></i></div>
    <div class="qz-num">${pad2(i + 1)}</div>
    <h2 class="qz-question">${Q.q}</h2>
    <div class="qz-opts">${opts}</div>
    <div class="qz-fb ${answered ? (ok ? 'show ok' : 'show bad') : ''}">
      <div class="qz-fbt">→ ${ok ? '¡CORRECTO!' : 'ESTA VEZ NO'}</div><p>${Q.e}</p>
    </div>
    <button class="qz-btn ${answered ? '' : 'hidden'}" data-act="next">${i + 1 < QZ_QUESTIONS.length ? 'SIGUIENTE PREGUNTA →' : 'VER MI RESULTADO →'}</button>
  </div>`;
}

function qzResultView(score) {
  const lv = qzLevel(score);
  const rows = [...QZ_LEVELS].reverse().map(l =>
    `<li class="${l === lv ? 'me' : ''}"><span>${l.name}</span><span>${l.min}+ pts</span></li>`).join('');
  return `<div class="qz-screen qz-res">
    <div class="qz-meta"><span>RESULTADO FINAL</span><span class="qz-pts"><i class="qz-dot"></i>COMPLETO</span></div>
    <div class="qz-score"><b>${score}</b><span>/ ${QZ_QUESTIONS.length}</span></div>
    <div class="qz-kicker">TU NIVEL</div>
    <div class="qz-level">${lv.name}</div>
    <p class="qz-desc">${lv.d}</p>
    <div class="qz-kicker">— RANKING</div>
    <ol class="qz-rank">${rows}</ol>
    <button class="qz-btn" data-act="restart">REPETIR DESAFÍO →</button>
  </div>`;
}
