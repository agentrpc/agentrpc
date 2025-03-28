import { OpenAI } from 'openai';
import { AgentRPC } from 'agentrpc';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const rpc = new AgentRPC({ apiSecret: process.env.AGENTRPC_API_SECRET });

const main = async () => {
  const tools = await rpc.OpenAI.getTools();
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'What is the weather in Melbourne?',
      },
    ],
    tools,
  });

  const message = completion.choices[0]?.message;

  if (message?.tool_calls) {
    for (const toolCall of message.tool_calls) {
      console.log('Agent is calling Tool', toolCall.function.name);
      const result = await rpc.OpenAI.executeTool(toolCall);
      console.log(result);
    }
  }
};

main();
