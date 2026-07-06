#!/bin/bash

# 创建重构项目目录结构
mkdir -p data_agent_refactored/{backend,frontend}

# 后端目录结构
mkdir -p data_agent_refactored/backend/{app/{api/{v1/{routers,dependencies},v2},core,models,schemas,services,utils},tests,scripts}

# 前端目录结构
mkdir -p data_agent_refactored/frontend/{src/{components,pages,hooks,services,store,utils,types,assets/{images,styles}},public}

echo "Project structure created successfully!"
