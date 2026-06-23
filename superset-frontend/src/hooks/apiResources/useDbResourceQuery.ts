/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { useCallback, useEffect } from 'react';
import { ClientErrorObject } from '@superset-ui/core';
import useEffectEvent from 'src/hooks/useEffectEvent';

interface TriggerResult<T> {
  isSuccess: boolean;
  isError: boolean;
  data?: T;
}

interface QueryResult<T> {
  isError: boolean;
  error?: unknown;
  currentData?: T;
  data?: T;
}

export type DbResourceOption = {
  value: string;
  label: string;
  title: string;
};

/**
 * Shared hook that wires up RTK Query lazy-trigger + cached-query with
 * error forwarding, auto-fetch on dependency change, and a ``refetch``
 * callback. Both ``useCatalogs`` and ``useSchemas`` delegate to this hook.
 *
 * @param trigger      RTK lazy query trigger function
 * @param result       RTK cached query result object
 * @param emptyDefault empty array constant used when the API returns no data
 * @param deps         list of dependency values (e.g. ``[dbId]`` or ``[dbId, catalog]``);
 *                     changes trigger a new fetch
 * @param onSuccess    optional callback fired after a successful fetch
 * @param onError      optional callback fired on error
 * @param skip         when true, suppress fetching
 */
export function useDbResourceQuery<T>(
  trigger: (args: Record<string, unknown>) => Promise<TriggerResult<T>>,
  result: QueryResult<T>,
  emptyDefault: T,
  deps: Record<string, unknown>,
  onSuccess?: (data: T, isRefetched: boolean) => void,
  onError?: (error: ClientErrorObject) => void,
  skip?: boolean,
) {
  useEffect(() => {
    if (result.isError) {
      onError?.(result.error as ClientErrorObject);
    }
  }, [result.isError, result.error, onError]);

  const fetchData = useEffectEvent((forceRefresh = false) => {
    if (!skip && (!result.currentData || forceRefresh)) {
      trigger({ ...deps, forceRefresh }).then(
        ({ isSuccess, isError, data }) => {
          if (isSuccess) {
            onSuccess?.(data ?? emptyDefault, forceRefresh);
          }
          if (isError) {
            onError?.(result.error as ClientErrorObject);
          }
        },
      );
    }
  });

  const refetch = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  const depValues = Object.values(deps);

  useEffect(() => {
    fetchData(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...depValues, fetchData]);

  return {
    ...result,
    refetch,
  };
}
