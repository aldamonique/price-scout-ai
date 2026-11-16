import Ajv2020, { type ValidateFunction } from 'ajv/dist/2020'

import openapi from './openapi.json'
import type { components } from './schema'

export type SchemaName = keyof components['schemas']
export type SchemaOf<Name extends SchemaName> = components['schemas'][Name]

const ajv = new Ajv2020({ strict: false, validateFormats: false, validateSchema: false, allErrors: false })
ajv.addSchema(openapi, 'openapi')

const cache = new Map<string, ValidateFunction>()

function validator(name: SchemaName, list: boolean): ValidateFunction {
  const key = `${name}${list ? '[]' : ''}`
  let validate = cache.get(key)
  if (!validate) {
    const ref = { $ref: `openapi#/components/schemas/${name}` }
    validate = ajv.compile(list ? { type: 'array', items: ref } : ref)
    cache.set(key, validate)
  }
  return validate
}

export class ResponseShapeError extends Error {
  constructor(name: string, detail: string) {
    super(`The API sent an unexpected ${name}: ${detail}`)
    this.name = 'ResponseShapeError'
  }
}

function explain(validate: ValidateFunction): string {
  const error = validate.errors?.[0]
  if (!error) return 'invalid data'
  return `${error.instancePath || '(root)'} ${error.message ?? 'is invalid'}`
}

export function parse<Name extends SchemaName>(name: Name, data: unknown): SchemaOf<Name> {
  const validate = validator(name, false)
  if (!validate(data)) throw new ResponseShapeError(name, explain(validate))
  return data as SchemaOf<Name>
}

export function parseList<Name extends SchemaName>(name: Name, data: unknown): SchemaOf<Name>[] {
  const validate = validator(name, true)
  if (!validate(data)) throw new ResponseShapeError(`${name} list`, explain(validate))
  return data as SchemaOf<Name>[]
}
