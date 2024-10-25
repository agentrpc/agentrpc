// https://github.com/sindresorhus/serialize-error/blob/main/index.js

const list = [
  // Native ES errors https://262.ecma-international.org/12.0/#sec-well-known-intrinsic-objects
  EvalError,
  RangeError,
  ReferenceError,
  SyntaxError,
  TypeError,
  URIError,

  // Built-in errors
  globalThis.DOMException,

  // Node-specific errors
  // https://nodejs.org/api/errors.html
  globalThis.AssertionError,
  globalThis.SystemError,
]
  // Non-native Errors are used with `globalThis` because they might be missing. This filter drops them when undefined.
  .filter(Boolean)
  .map((constructor) => [constructor.name, constructor]);

const errorConstructors = new Map(list);

export class NonError extends Error {
  name = "NonError";

  constructor(message) {
    super(NonError._prepareSuperMessage(message));
  }

  static _prepareSuperMessage(message) {
    try {
      return JSON.stringify(message);
    } catch {
      return String(message);
    }
  }
}

const commonProperties = [
  {
    property: "name",
    enumerable: false,
  },
  {
    property: "message",
    enumerable: false,
  },
  {
    property: "stack",
    enumerable: false,
  },
  {
    property: "code",
    enumerable: true,
  },
  {
    property: "cause",
    enumerable: false,
  },
  {
    property: "response",
    enumerable: false,
  },
  {
    property: "request",
    enumerable: false,
  },
];

const toJsonWasCalled = new WeakSet();

const toJSON = (from) => {
  toJsonWasCalled.add(from);
  const json = from.toJSON();
  toJsonWasCalled.delete(from);
  return json;
};

const getErrorConstructor = (name) => errorConstructors.get(name) ?? Error;

// eslint-disable-next-line complexity
const destroyCircular = ({
  from,
  seen,
  to,
  forceEnumerable,
  maxDepth,
  depth,
  useToJSON,
  serialize,
}) => {
  if (!to) {
    if (Array.isArray(from)) {
      to = [];
    } else if (!serialize && isErrorLike(from)) {
      const Error = getErrorConstructor(from.name);
      to = new Error();
    } else {
      to = {};
    }
  }

  seen.push(from);

  if (depth >= maxDepth) {
    return to;
  }

  if (
    useToJSON &&
    typeof from.toJSON === "function" &&
    !toJsonWasCalled.has(from)
  ) {
    return toJSON(from);
  }

  const continueDestroyCircular = (value) =>
    destroyCircular({
      from: value,
      seen: [...seen],
      forceEnumerable,
      maxDepth,
      depth,
      useToJSON,
      serialize,
    });

  for (const [key, value] of Object.entries(from)) {
    // eslint-disable-next-line node/prefer-global/buffer
    if (typeof Buffer === "function" && Buffer.isBuffer(value)) {
      to[key] = "[object Buffer]";
      continue;
    }

    // TODO: Use `stream.isReadable()` when targeting Node.js 18.
    if (
      value !== null &&
      typeof value === "object" &&
      typeof value.pipe === "function"
    ) {
      to[key] = "[object Stream]";
      continue;
    }

    if (typeof value === "function") {
      continue;
    }

    if (!value || typeof value !== "object") {
      to[key] = value;
      continue;
    }

    if (!seen.includes(from[key])) {
      depth++;
      to[key] = continueDestroyCircular(from[key]);

      continue;
    }

    to[key] = "[Circular]";
  }

  for (const { property, enumerable } of commonProperties) {
    if (typeof from[property] !== "undefined" && from[property] !== null) {
      Object.defineProperty(to, property, {
        value: isErrorLike(from[property])
          ? continueDestroyCircular(from[property])
          : from[property],
        enumerable: forceEnumerable ? true : enumerable,
        configurable: true,
        writable: true,
      });
    }
  }

  return to;
};

export function serializeError(value, options = {}) {
  const { maxDepth = Number.POSITIVE_INFINITY, useToJSON = true } = options;

  if (typeof value === "object" && value !== null) {
    return destroyCircular({
      from: value,
      seen: [],
      forceEnumerable: true,
      maxDepth,
      depth: 0,
      useToJSON,
      serialize: true,
    });
  }

  // People sometimes throw things besides Error objects…
  if (typeof value === "function") {
    // `JSON.stringify()` discards functions. We do too, unless a function is thrown directly.
    return `[Function: ${value.name ?? "anonymous"}]`;
  }

  return value;
}

export function isErrorLike(value) {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    "name" in value &&
    "message" in value &&
    "stack" in value
  );
}

function isMinimumViableSerializedError(value) {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    "message" in value &&
    !Array.isArray(value)
  );
}
