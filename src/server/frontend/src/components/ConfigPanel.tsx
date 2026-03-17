/**
 * ConfigPanel Component
 *
 * Collapsible sidebar showing agent configuration details.
 */
import { type FC, useState } from 'react';
import {
  AgentConfig,
  ToolInfo,
  SkillInfo,
  SubagentInfo,
} from '../api/client';

interface ConfigPanelProps {
  name: string;
  description: string;
  config: AgentConfig;
  tools: ToolInfo[];
  skills: SkillInfo[];
  subagents: SubagentInfo[];
}

export const ConfigPanel: FC<ConfigPanelProps> = ({
  name,
  description,
  config,
  tools,
  skills,
  subagents,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const sections = [
    { key: 'tools', label: 'Tools', count: tools.length, items: tools },
    { key: 'skills', label: 'Skills', count: skills.length, items: skills },
    { key: 'subagents', label: 'Subagents', count: subagents.length, items: subagents },
    { key: 'config', label: 'Configuration', count: 0, isConfig: true },
  ].filter((s) => s.count > 0 || s.isConfig);

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-gray-800 text-white px-2 py-4 rounded-l-lg hover:bg-gray-700 transition-colors z-40"
        style={{ right: isOpen ? '320px' : '0' }}
      >
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full bg-white border-l border-gray-200 shadow-lg transition-transform duration-300 z-30 overflow-y-auto ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ width: '320px' }}
      >
        <div className="p-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">{name}</h2>
            <p className="text-sm text-gray-600">{description}</p>
          </div>

          <div className="space-y-3">
            {sections.map((section) => (
              <div key={section.key} className="border border-gray-200 rounded-lg">
                <button
                  onClick={() =>
                    setExpandedSection(expandedSection === section.key ? null : section.key)
                  }
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <span className="font-medium text-gray-900">
                    {section.label}
                    {section.count > 0 && <span className="ml-2 text-gray-500">({section.count})</span>}
                  </span>
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedSection === section.key ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {expandedSection === section.key && (
                  <div className="px-4 pb-3 border-t border-gray-100">
                    {section.isConfig ? (
                      <div className="text-sm text-gray-600 space-y-2 mt-3">
                        <div>
                          <span className="font-medium">Max Steps:</span> {config.max_steps}
                        </div>
                        {config.workspace_root && (
                          <div>
                            <span className="font-medium">Workspace:</span> {config.workspace_root}
                          </div>
                        )}
                        {config.experience_enabled && (
                          <div className="text-green-600">
                            <span className="font-medium">Experience System:</span> Enabled
                          </div>
                        )}
                        {config.knowledge_base && (
                          <div>
                            <span className="font-medium">Knowledge Base:</span> Configured
                          </div>
                        )}
                      </div>
                    ) : section.items ? (
                      <div className="mt-3 space-y-2">
                        {section.items.map((item: any, index: number) => (
                          <div key={index} className="text-sm">
                            <div className="font-medium text-gray-900">{item.name}</div>
                            <div className="text-gray-600 text-xs">{item.description}</div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};
