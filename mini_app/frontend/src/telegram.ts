export const getTelegramInitData = (): string => {
  // @ts-ignore
  const tg = window.Telegram?.WebApp
  if (!tg) return ''
  tg.ready()
  tg.expand()
  return tg.initData || ''
}
