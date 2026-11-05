---
name: editor-reels-claseflix
description: Edita Reels verticales en español del creador siguiendo su padrão fijo (cortes de silencios y errores, subtítulos, split screen con b-roll en loop, chat de Claude en dark mode, palabra clave del CTA, sound design discreto y márgenes de Instagram). Úsala cuando el usuario envíe un vídeo base del creador y una referencia o b-roll para editar.
---

# Padrão de edição de Reels (criador em espanhol)

## Entrega
- 1080x1920, 30 fps, H.264, áudio AAC, voz normalizada a -14 LUFS.
- Salvar em reels/<tema>_vN.mp4 com o script de render; commit + push no branch da sessão.
- Enviar prévia leve (<30 MB) e dizer em 1ª linha o que mudou.
- Cada ajuste pedido = nova versão (v2, v3...), sem apagar as anteriores.

## Cortes
- Remover silêncios e respirações longas (sem zoom ou mudança de escala no rosto).
- Remover gaguejos, palavras erradas e tomadas repetidas: manter só a versão correta
  da frase. Conferir cada corte com transcrição antes de renderizar.
- Sem "pedaços" de sílaba nem buracos de silêncio digital nos cortes.

## Legendas
- InterDisplay Bold branca, minúscula, 1–3 palavras, sombra escura desfocada.
- Nomes de ferramentas e destaques em caixa vermelha arredondada.
- Nunca sobre o rosto. No split: na emenda entre os painéis. Tela cheia: no peito,
  ou no topo quando o rosto ocupar a parte de baixo.

## Margens do Instagram (nada encosta)
- Área segura x 46–1033, y 115–1544; barra do topo x 313–762, y 132–216 livre;
  coluna de ícones da direita (x ≥ 886, y 960–1524) sem texto.
- Conferir frames de prévia contra a grade antes do render final.

## Layout
- Split screen: painel de cima com o conteúdo, ele embaixo com o rosto centralizado.
- B-roll enviado: card arredondado dentro das margens, fundo = o mesmo vídeo borrado
  e escuro (discreto), em loop até ele terminar de falar, sem som (ou bem baixo se eu pedir).
  Pular trechos congelados do b-roll.
- Telas/interfaces: fiéis ao vídeo de referência. Conceitos complexos: animação 3D clara. (se necessários)
- Chat do Claude: idêntico ao atual, modo escuro, interface em espanhol, prompt digitado
  em sincronia com a fala, centralizado e grande, zoom leve + motion blur.
- Se ele falar de outra IA (ChatGPT etc.), perguntar antes qual marca usar.

## Palavra-chave do CTA
- Grande, em caixa vermelha, no topo; nesse momento só ele, a legenda e a palavra
  (nenhuma imagem extra); legendas escondidas ~1 s.
- Confirmar a palavra com duas transcrições; se houver dúvida, perguntar.

## Som
- Discreto: whoosh suave e abafado, plucks graves, boom grave na palavra-chave.
- Nunca sons agudos/rápidos nem "vento" ruidoso. Na dúvida, mostrar opções antes.

## Assets
- Perguntar antes de finalizar quando algo for ambíguo.
