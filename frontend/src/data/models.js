// 静态模型数据配置
export const staticModels = {
  regression: {
    linear_regression: {
      id: 'linear_regression',
      name: '线性回归',
      type: 'regression',
      description: '适用于连续型地质数据的线性关系建模',
      parameters: {
        fit_intercept: {
          type: 'bool',
          description: '是否计算截距',
          default_value: true,
          help: '如果为False，则不会计算截距（即数据应该已经居中）'
        },
        normalize: {
          type: 'bool',
          description: '是否标准化特征',
          default_value: false,
          help: '在拟合前是否标准化回归变量'
        },
        copy_X: {
          type: 'bool',
          description: '是否复制X',
          default_value: true,
          help: '是否复制X，否则可能会被覆盖'
        },
        n_jobs: {
          type: 'int',
          description: '并行作业数',
          default_value: 1,
          min_value: 1,
          max_value: 16,
          help: '用于计算的作业数'
        }
      }
    },
    ridge_regression: {
      id: 'ridge_regression',
      name: '岭回归',
      type: 'regression',
      description: '带L2正则化的线性回归，适用于多重共线性数据',
      parameters: {
        alpha: {
          type: 'float',
          description: '正则化强度',
          default_value: 1.0,
          min_value: 0.0,
          max_value: 10.0,
          help: '正则化参数，控制模型复杂度'
        },
        fit_intercept: {
          type: 'bool',
          description: '是否计算截距',
          default_value: true,
          help: '是否计算此模型的截距'
        },
        normalize: {
          type: 'bool',
          description: '是否标准化特征',
          default_value: false,
          help: '在拟合前是否标准化回归变量'
        },
        solver: {
          type: 'string',
          description: '求解器',
          default_value: 'auto',
          options: ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga'],
          help: '用于计算的求解器'
        }
      }
    },
    lasso_regression: {
      id: 'lasso_regression',
      name: 'Lasso回归',
      type: 'regression',
      description: '带L1正则化的线性回归，适用于特征选择',
      parameters: {
        alpha: {
          type: 'float',
          description: '正则化强度',
          default_value: 1.0,
          min_value: 0.0,
          max_value: 10.0,
          help: '正则化参数，控制模型复杂度'
        },
        fit_intercept: {
          type: 'bool',
          description: '是否计算截距',
          default_value: true,
          help: '是否计算此模型的截距'
        },
        normalize: {
          type: 'bool',
          description: '是否标准化特征',
          default_value: false,
          help: '在拟合前是否标准化回归变量'
        },
        max_iter: {
          type: 'int',
          description: '最大迭代次数',
          default_value: 1000,
          min_value: 100,
          max_value: 10000,
          help: '最大迭代次数'
        }
      }
    },
    random_forest_regression: {
      id: 'random_forest_regression',
      name: '随机森林回归',
      type: 'regression',
      description: '集成学习方法，适用于复杂非线性关系建模',
      parameters: {
        n_estimators: {
          type: 'int',
          description: '树的数量',
          default_value: 100,
          min_value: 10,
          max_value: 1000,
          help: '森林中树的数量'
        },
        max_depth: {
          type: 'int',
          description: '最大深度',
          default_value: 10,
          min_value: 1,
          max_value: 50,
          help: '树的最大深度'
        },
        min_samples_split: {
          type: 'int',
          description: '最小分裂样本数',
          default_value: 2,
          min_value: 2,
          max_value: 20,
          help: '分裂内部节点所需的最小样本数'
        },
        min_samples_leaf: {
          type: 'int',
          description: '最小叶子样本数',
          default_value: 1,
          min_value: 1,
          max_value: 10,
          help: '叶节点所需的最小样本数'
        }
      }
    }
  },
  clustering: {
    kmeans: {
      id: 'kmeans',
      name: 'K均值聚类',
      type: 'clustering',
      description: '经典聚类算法，适用于地质数据分类',
      parameters: {
        n_clusters: {
          type: 'int',
          description: '聚类数量',
          default_value: 3,
          min_value: 2,
          max_value: 20,
          help: '要形成的聚类数量'
        },
        init: {
          type: 'string',
          description: '初始化方法',
          default_value: 'k-means++',
          options: ['k-means++', 'random'],
          help: '初始化方法：k-means++或random'
        },
        n_init: {
          type: 'int',
          description: '运行次数',
          default_value: 10,
          min_value: 1,
          max_value: 100,
          help: '使用不同质心种子运行k-means的次数'
        },
        max_iter: {
          type: 'int',
          description: '最大迭代次数',
          default_value: 300,
          min_value: 100,
          max_value: 1000,
          help: '单次运行的最大迭代次数'
        }
      }
    },
    dbscan: {
      id: 'dbscan',
      name: 'DBSCAN聚类',
      type: 'clustering',
      description: '基于密度的聚类算法，适用于不规则形状的聚类',
      parameters: {
        eps: {
          type: 'float',
          description: '邻域半径',
          default_value: 0.5,
          min_value: 0.1,
          max_value: 10.0,
          help: '邻域搜索的半径'
        },
        min_samples: {
          type: 'int',
          description: '最小样本数',
          default_value: 5,
          min_value: 1,
          max_value: 50,
          help: '形成核心点所需的邻域内最小样本数'
        },
        metric: {
          type: 'string',
          description: '距离度量',
          default_value: 'euclidean',
          options: ['euclidean', 'manhattan', 'cosine'],
          help: '计算点之间距离的度量'
        }
      }
    },
    hierarchical_clustering: {
      id: 'hierarchical_clustering',
      name: '层次聚类',
      type: 'clustering',
      description: '构建聚类层次结构的算法',
      parameters: {
        n_clusters: {
          type: 'int',
          description: '聚类数量',
          default_value: 3,
          min_value: 2,
          max_value: 20,
          help: '要形成的聚类数量'
        },
        linkage: {
          type: 'string',
          description: '链接方法',
          default_value: 'ward',
          options: ['ward', 'complete', 'average', 'single'],
          help: '用于计算簇间距离的链接方法'
        },
        metric: {
          type: 'string',
          description: '距离度量',
          default_value: 'euclidean',
          options: ['euclidean', 'manhattan', 'cosine'],
          help: '计算点之间距离的度量'
        }
      }
    }
  },
  classification: {
    logistic_regression: {
      id: 'logistic_regression',
      name: '逻辑回归',
      type: 'classification',
      description: '适用于二分类问题的线性分类器',
      parameters: {
        C: {
          type: 'float',
          description: '正则化强度',
          default_value: 1.0,
          min_value: 0.1,
          max_value: 10.0,
          help: '正则化强度的倒数'
        },
        penalty: {
          type: 'string',
          description: '正则化类型',
          default_value: 'l2',
          options: ['l1', 'l2', 'elasticnet', 'none'],
          help: '使用的正则化类型'
        },
        solver: {
          type: 'string',
          description: '求解器',
          default_value: 'lbfgs',
          options: ['lbfgs', 'liblinear', 'newton-cg', 'sag', 'saga'],
          help: '用于优化的算法'
        },
        max_iter: {
          type: 'int',
          description: '最大迭代次数',
          default_value: 100,
          min_value: 50,
          max_value: 1000,
          help: '最大迭代次数'
        }
      }
    },
    random_forest_classification: {
      id: 'random_forest_classification',
      name: '随机森林分类',
      type: 'classification',
      description: '集成分类器，适用于复杂分类问题',
      parameters: {
        n_estimators: {
          type: 'int',
          description: '树的数量',
          default_value: 100,
          min_value: 10,
          max_value: 1000,
          help: '森林中树的数量'
        },
        max_depth: {
          type: 'int',
          description: '最大深度',
          default_value: 10,
          min_value: 1,
          max_value: 50,
          help: '树的最大深度'
        },
        criterion: {
          type: 'string',
          description: '分裂标准',
          default_value: 'gini',
          options: ['gini', 'entropy'],
          help: '分裂质量的标准'
        },
        min_samples_split: {
          type: 'int',
          description: '最小分裂样本数',
          default_value: 2,
          min_value: 2,
          max_value: 20,
          help: '分裂内部节点所需的最小样本数'
        }
      }
    }
  },
  time_series: {
    arima: {
      id: 'arima',
      name: 'ARIMA模型',
      type: 'time_series',
      description: '自回归积分移动平均模型，适用于时间序列预测',
      parameters: {
        p: {
          type: 'int',
          description: 'AR阶数',
          default_value: 1,
          min_value: 0,
          max_value: 10,
          help: '自回归项的阶数'
        },
        d: {
          type: 'int',
          description: '差分阶数',
          default_value: 1,
          min_value: 0,
          max_value: 5,
          help: '差分阶数'
        },
        q: {
          type: 'int',
          description: 'MA阶数',
          default_value: 1,
          min_value: 0,
          max_value: 10,
          help: '移动平均项的阶数'
        },
        seasonal_order: {
          type: 'string',
          description: '季节性阶数',
          default_value: '(0,0,0,0)',
          help: '季节性ARIMA参数 (P,D,Q,s)'
        }
      }
    },
    exponential_smoothing: {
      id: 'exponential_smoothing',
      name: '指数平滑',
      type: 'time_series',
      description: '适用于趋势和季节性时间序列预测',
      parameters: {
        trend: {
          type: 'string',
          description: '趋势类型',
          default_value: 'add',
          options: ['add', 'mul', 'additive', 'multiplicative'],
          help: '趋势类型'
        },
        seasonal: {
          type: 'string',
          description: '季节性类型',
          default_value: 'add',
          options: ['add', 'mul', 'additive', 'multiplicative'],
          help: '季节性类型'
        },
        seasonal_periods: {
          type: 'int',
          description: '季节性周期',
          default_value: 12,
          min_value: 2,
          max_value: 52,
          help: '季节性周期长度'
        }
      }
    }
  }
}



// 获取模型分类列表
export const getModelCategories = () => {
  return [
    { id: 'regression', name: '回归模型', icon: 'TrendCharts' },
    { id: 'clustering', name: '聚类模型', icon: 'Grid' },
    { id: 'classification', name: '分类模型', icon: 'Collection' },
    { id: 'time_series', name: '时间序列', icon: 'Clock' }
  ]
}

// 获取指定分类的模型列表
export const getModelsByCategory = (category) => {
  return staticModels[category] || {}
}

// 获取所有模型
export const getAllModels = () => {
  return staticModels
}

 