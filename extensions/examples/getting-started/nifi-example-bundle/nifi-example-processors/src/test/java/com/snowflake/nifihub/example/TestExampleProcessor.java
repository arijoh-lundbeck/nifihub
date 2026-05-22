/*
 * Copyright 2026 Snowflake Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.snowflake.nifihub.example;

import org.apache.nifi.util.MockFlowFile;
import org.apache.nifi.util.TestRunner;
import org.apache.nifi.util.TestRunners;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class TestExampleProcessor {

    @Test
    void testAttributeAddedToFlowFile() {
        final TestRunner runner = TestRunners.newTestRunner(ExampleProcessor.class);
        runner.setProperty(ExampleProcessor.ATTRIBUTE_NAME, "greeting");
        runner.setProperty(ExampleProcessor.ATTRIBUTE_VALUE, "hello");

        runner.enqueue("test content");
        runner.run();

        runner.assertAllFlowFilesTransferred(ExampleProcessor.REL_SUCCESS, 1);
        final List<MockFlowFile> results = runner.getFlowFilesForRelationship(ExampleProcessor.REL_SUCCESS);
        assertEquals("hello", results.getFirst().getAttribute("greeting"));
    }

    @Test
    void testExpressionLanguageSupport() {
        final TestRunner runner = TestRunners.newTestRunner(ExampleProcessor.class);
        runner.setProperty(ExampleProcessor.ATTRIBUTE_NAME, "derived");
        runner.setProperty(ExampleProcessor.ATTRIBUTE_VALUE, "${filename}-processed");

        runner.enqueue("test content", java.util.Map.of("filename", "data"));
        runner.run();

        runner.assertAllFlowFilesTransferred(ExampleProcessor.REL_SUCCESS, 1);
        final List<MockFlowFile> results = runner.getFlowFilesForRelationship(ExampleProcessor.REL_SUCCESS);
        assertEquals("data-processed", results.getFirst().getAttribute("derived"));
    }

    @Test
    void testNoInputYieldsNoOutput() {
        final TestRunner runner = TestRunners.newTestRunner(ExampleProcessor.class);
        runner.setProperty(ExampleProcessor.ATTRIBUTE_NAME, "key");
        runner.setProperty(ExampleProcessor.ATTRIBUTE_VALUE, "value");

        runner.run();

        runner.assertTransferCount(ExampleProcessor.REL_SUCCESS, 0);
    }

    @Test
    void testMissingRequiredPropertyFailsValidation() {
        final TestRunner runner = TestRunners.newTestRunner(ExampleProcessor.class);
        runner.assertNotValid();

        runner.setProperty(ExampleProcessor.ATTRIBUTE_NAME, "key");
        runner.assertNotValid();

        runner.setProperty(ExampleProcessor.ATTRIBUTE_VALUE, "value");
        runner.assertValid();
    }
}
