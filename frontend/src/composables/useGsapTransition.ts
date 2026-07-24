/**
 * useGsapTransition —— GSAP 驱动的路由/角色切换动效
 *
 * 设计目标（"领导点评级别"丝滑）：
 * 1. 路由切换：旧页淡出+轻微上移，新页元素 stagger 入场（卡片/标题/菜单依次浮起）
 * 2. 主题切换：CSS 变量颜色平滑过渡（GSAP 插值 hex/oklch），让换系统时主色"流"过去
 * 3. 侧栏/菜单：进入时从左到右 stagger 滑入
 *
 * 用法（在 RoleLayout 或 App.vue 里）：
 *   const { enterPage, transitionTheme } = useGsapTransition()
 *   onMounted(() => enterPage(containerRef.value))
 *
 * 按 gsap-frameworks 规范：用 gsap.context(scope) 限定选择器，onUnmounted 调 ctx.revert()。
 */
import { onUnmounted } from 'vue'
import { gsap } from 'gsap'

let ctx: gsap.Context | null = null

/**
 * 卡片/面板入场 stagger 目标（覆盖所有页面实际用到的容器类）：
 *  - .page-card  → report / review / resource / dispatch / system / audit
 *  - .panel      → dashboard 的子区块
 *  - .stats      → dashboard 的指标条
 *  - .cmdbar     → dashboard 的命令栏
 *  - .kpi        → dispatch 的指标块
 *  - .comp       → plan 的 AI 区块
 *  - .kb         → knowledge 知识库容器
 *  - .sys        → system 容器
 *  - .audit      → audit 容器
 *  - .resource / .dispatch / .review / .report / .dashboard → 各页根容器
 */
const CARD_SELECTORS = [
  '.page-card',
  '.panel',
  '.stats',
  '.cmdbar',
  '.kpi',
  '.comp',
  '.kb',
  '.sys',
  '.audit',
  '.resource',
  '.dispatch',
  '.review',
  '.report',
  '.dashboard'
].join(', ')

export function useGsapTransition() {
  /**
   * 页面/路由进入动画：容器内所有"卡片类"元素依次浮起
   * @param root 容器元素（ref.value），所有选择器都限定在此子树内
   */
  function enterPage(root: HTMLElement | null | undefined) {
    if (!root) return
    // 清理上一次的 context（避免切换多次后残留）
    ctx?.revert()
    ctx = gsap.context(() => {
      // 1. 容器整体淡入
      gsap.from(root, {
        opacity: 0,
        duration: 0.32,
        ease: 'power2.out'
      })

      // 2. 所有"卡片/面板/根容器" stagger 入场（从下方浮起 + 淡入）
      gsap.from(CARD_SELECTORS, {
        y: 28,
        opacity: 0,
        duration: 0.55,
        ease: 'power3.out',
        stagger: 0.09,
        clearProps: 'opacity,transform'
      })

      // 3. 区块标题左滑入（覆盖 dashboard/plan/system/audit 等所有标题类）
      gsap.from('.section-title, .cmd-title, .panel-title, .block-title', {
        x: -18,
        opacity: 0,
        duration: 0.42,
        ease: 'power2.out',
        stagger: 0.05
      })

      // 4. 菜单项 stagger（侧栏从上到下依次滑入）
      gsap.from('.el-menu-item', {
        x: -24,
        opacity: 0,
        duration: 0.38,
        ease: 'power2.out',
        stagger: 0.05
      })

      // 5. 角色签名徽章弹一下
      gsap.from('.role-signature', {
        scale: 0.5,
        opacity: 0,
        duration: 0.55,
        ease: 'back.out(1.8)'
      })

      // 6. dashboard 指标卡微缩放入场（错峰，更"领导点评"）
      gsap.from('.stats .item, .kpi', {
        scale: 0.92,
        opacity: 0,
        duration: 0.45,
        ease: 'power2.out',
        stagger: 0.06,
        delay: 0.1
      })
    }, root)
  }

  /**
   * 主题色平滑过渡：换系统时主色"流"过去
   * 调用时机：角色切换后（watch roleKey）
   */
  function transitionTheme() {
    // body 背景由 CSS 变量驱动，做 brightness/saturate 脉冲让用户感知到"换装"
    gsap.fromTo('body',
      { filter: 'brightness(1.10) saturate(1.18)' },
      {
        filter: 'brightness(1) saturate(1)',
        duration: 0.7,
        ease: 'power2.out'
      }
    )
    // 配合 role-shell 轻微缩放呼吸，强化切换仪式感
    gsap.fromTo('.role-shell',
      { scale: 0.985 },
      { scale: 1, duration: 0.55, ease: 'power3.out' }
    )
  }

  /**
   * 登录过渡：登录卡片缩小淡出，准备进入工作台
   * @param el 登录页根元素
   */
  function exitLogin(el: HTMLElement | null | undefined, done?: () => void) {
    if (!el) { done?.(); return }
    gsap.to(el, {
      opacity: 0,
      scale: 0.96,
      filter: 'blur(8px)',
      duration: 0.45,
      ease: 'power2.in',
      onComplete: () => done?.()
    })
  }

  onUnmounted(() => {
    ctx?.revert()
    ctx = null
  })

  return { enterPage, transitionTheme, exitLogin }
}