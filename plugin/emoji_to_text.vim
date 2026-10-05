" EmojiToText: convert the whole buffer's emoji to :shortcode:.
if exists('g:loaded_emoji_to_text')
  finish
endif
let g:loaded_emoji_to_text = 1

" Ignore any range silently; the engine always acts on the whole buffer.
command! -bar -range=% EmojiToText call emoji_to_text#convert()
