    // 构建请求
    const request = {
      user_request: `为${configForm.systemName}生成测试用例`,
      context: {
        system_name: configForm.systemName,
        tara_result: inputTaraResult,
        system_info: configForm.systemInfo,
        test_type: configForm.testType,
        target_systems: configForm.targetSystems,
        threat_sources: configForm.threatSources,
        priority_filter: configForm.priorityFilter,
        output_format: configForm.outputFormat,
        generation_type: 'test_cases'
      },
      timeout: 300,
      stream: false,
      // 添加缺失的参数
      priority: "normal",
      metadata: {
        source: "testcase_ui",
        version: "1.0"
      },
      enable_planning: true,
      step_by_step: true,
      chat_mode: false,
      agent_config: {
        model: "default"
      }
    } 