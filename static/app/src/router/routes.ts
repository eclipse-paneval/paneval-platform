import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/PublicLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/pages/home/HomePage.vue'),
        meta: {
          titleKey: 'router.home'
        }
      }
    ]
  },
  {
    path: '/mine',
    redirect: '/'
  },
  {
    path: '/console',
    component: () => import('@/layouts/ConsoleLayout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'console-home',
        redirect: '/console/evaluations'
      },
      {
        path: 'evaluations',
        name: 'console-evaluations',
        component: () => import('@/pages/console/evaluations/EvaluationListPage.vue'),
        meta: {
          titleKey: 'router.evaluationManage',
          keepAlive: true
        }
      },
      {
        path: 'evaluations/create',
        name: 'console-evaluation-create',
        component: () => import('@/pages/console/evaluations/EvaluationCreatePage.vue'),
        meta: {
          titleKey: 'router.createEvaluation'
        }
      },
      {
        path: 'evaluations/:id/edit',
        name: 'console-evaluation-edit',
        component: () => import('@/pages/console/evaluations/EvaluationCreatePage.vue'),
        meta: {
          titleKey: 'router.editEvaluation'
        }
      },
      {
        path: 'evaluations/:id',
        name: 'console-evaluation-detail',
        component: () => import('@/pages/console/evaluations/EvaluationDetailPage.vue'),
        meta: {
          titleKey: 'router.evaluationDetail'
        }
      },
      {
        path: 'images',
        name: 'console-images',
        component: () => import('@/pages/console/images/ImagesListPage.vue'),
        meta: {
          titleKey: 'router.imagesManage'
        }
      },
      {
        path: 'images/create',
        name: 'console-image-create',
        component: () => import('@/pages/console/images/ImageCreatePage.vue'),
        meta: {
          titleKey: 'router.createImage'
        }
      }
    ]
  }
]
