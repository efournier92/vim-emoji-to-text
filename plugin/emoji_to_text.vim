" EmojiToText: convert emoji to :shortcode: over the whole buffer or a range.
if exists('g:loaded_emoji_to_text')
  finish
endif
let g:loaded_emoji_to_text = 1

" No range converts the whole buffer; a range converts only those lines.
command! -bar -range=% EmojiToText call emoji_to_text#convert(<line1>, <line2>)
